#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <structmember.h>

#include <inttypes.h>
#include <stddef.h>
#include <stdio.h>
#include <sys/syscall.h>
#include <linux/perf_event.h>

// Python stuff
static PyMethodDef PerfMethods[] = {
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


/*
known rapl_domain_names
	"energy-cores",
	"energy-gpu",
	"energy-pkg",
	"energy-ram",
	"energy-psys",
*/

typedef struct {
    char* name;
    int event_id;
    double scale;
    int units; 
} RAPLconfig;

typedef struct {
    PyObject_HEAD
    int perf_paranoia_level;
    int max_package_id;
    int power_event_type;
    long** perf_fd;
    Py_ssize_t n_rapl_domains;
    RAPLconfig* config;
    int* pack_cpu_id;
    double last_energy;
} PerfObject;

static struct PyModuleDef perfmodule = {
    PyModuleDef_HEAD_INIT,
    "perf",   /* name of module */
    NULL, /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module,
                 or -1 if the module keeps state in global variables. */
    PerfMethods
};

static PyObject* perf_start(PerfObject *self, PyObject *args);
static PyObject* perf_stop(PerfObject *self, PyObject *args);
static PyObject* perf_delta(PerfObject *self, PyObject *args);

// Define perf_event_open syscall wrapper
static long perf_event_open(struct perf_event_attr *hw_event, pid_t pid, int cpu, int group_fd, unsigned long flags) {  return syscall(__NR_perf_event_open, hw_event, pid, cpu, group_fd, flags); }  

static void Perf_dealloc(PerfObject* self)
{
    for (int i = 0; i < self->max_package_id; i++)
    {
        free(self->perf_fd[i]);
    }
    free(self->perf_fd);
    for (int i = 0; i < self->n_rapl_domains; i++) {
        free(self->config[i].name);
    }
    free(self->config);
    free(self->pack_cpu_id);

    Py_TYPE(self)->tp_free((PyObject*) self);
}

static PyObject* Perf_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    PerfObject* self;
    if ((self = (PerfObject *) type->tp_alloc(type, 0)) != NULL) {
        self->perf_paranoia_level = INT_MAX;
        self->max_package_id = -1;
        self->power_event_type = -1;
        self->perf_fd = NULL;
    }
    return (PyObject*) self;
}

static int Perf_init(PerfObject *self, PyObject *args, PyObject *kwds)
{
    PyObject* py_list;
    if (!PyArg_ParseTuple(args, "O", &py_list)) {
        return -1;
    }
    self->n_rapl_domains = PyList_Size(py_list);
    self->config = (RAPLconfig*)malloc(sizeof(RAPLconfig)*self->n_rapl_domains);
    for (int i = 0; i < self->n_rapl_domains; i++) {
        PyObject* item; 
        if ((item = PyList_GetItem(py_list, i)) == NULL) {
            return -1;
        }
        self->config[i].name = strdup(PyBytes_AS_STRING(PyUnicode_AsUTF8String(item)));
    }

    // Check kernel perf paranoia level
    FILE* paranoid_file;
    if ((paranoid_file = fopen("/proc/sys/kernel/perf_event_paranoid","r")) == NULL) {
        PyErr_SetFromErrno(PyExc_IOError);
        return -1;
    }
    if (fscanf(paranoid_file, "%d", &self->perf_paranoia_level) == EOF) {
        PyErr_SetFromErrno(PyExc_IOError);
        return -1;
    }
    if (fclose(paranoid_file) != 0) {
        PyErr_SetFromErrno(PyExc_IOError);
        return -1;
    }

    // Check how many packages we have
    int packageid;
    ssize_t n_pack_cpu_id = 16;
    self->pack_cpu_id = (int*)malloc(n_pack_cpu_id*sizeof(int));
    self->pack_cpu_id[0] = 0;
    for (int cpuid = 0; cpuid < INT_MAX; cpuid++) {
        FILE* packfile;
        char* cpupath;
        if (asprintf(&cpupath, "/sys/devices/system/cpu/cpu%d/topology/physical_package_id", cpuid) == -1) {
            PyErr_SetFromErrno(PyExc_MemoryError);
            return -1;
        }
        if ((packfile = fopen(cpupath, "r"))== NULL) {
            free(cpupath);
            break; // No more CPUs
        }
        free(cpupath);
        if (fscanf(packfile,"%d",&packageid) == EOF) {
            PyErr_SetFromErrno(PyExc_IOError);
            return -1;
        }
        if (packageid > self->max_package_id) {
            self->max_package_id = packageid;
            if (n_pack_cpu_id == self->max_package_id) {
                n_pack_cpu_id += 16;
                self->pack_cpu_id = realloc(self->pack_cpu_id, n_pack_cpu_id*sizeof(int));
            }
            self->pack_cpu_id[packageid] = cpuid;
        }
        if (fclose(packfile) != 0) {
            PyErr_SetFromErrno(PyExc_IOError);
            return -1;
        }
    }
    if (self->max_package_id == -1) {
        PyErr_SetString(PyExc_Exception, "No CPU detected");
        return -1;
    }
    self->perf_fd = (long**)malloc(sizeof(long*)*(self->max_package_id+1));
    for (int i = 0; i <= self->max_package_id; i++)
    {
        self->perf_fd[i] = (long*)malloc(sizeof(long)*self->n_rapl_domains);
    }

    // If this isn't here we have an issue
    FILE* power_event_file;
    if ((power_event_file = fopen("/sys/bus/event_source/devices/power/type", "r")) == NULL) {
        PyErr_SetFromErrno(PyExc_IOError);
        return -1;
    }
    if ( fscanf(power_event_file, "%d", &self->power_event_type) == EOF) {
        PyErr_SetFromErrno(PyExc_IOError);
        return -1;
    }
    if (fclose(power_event_file) != 0) {
        PyErr_SetFromErrno(PyExc_IOError);
        return -1;
    }

    // Get scale and units for each event type
    for (int i = 0; i < self->n_rapl_domains; i++) {
        FILE* rapldomainfile;
        char* cpupath = NULL;
        if (asprintf(&cpupath, "/sys/bus/event_source/devices/power/events/%s", self->config[i].name) == -1) {
            PyErr_SetFromErrno(PyExc_MemoryError);
            return -1;
        }
        if ((rapldomainfile = fopen(cpupath, "r"))== NULL) {
            self->config[i].event_id = 0;
            free(cpupath);
            continue; // We don't support this event type so skip
        }
        if ( fscanf(rapldomainfile, "event=%x", &self->config[i].event_id) == EOF) {
            PyErr_SetFromErrno(PyExc_IOError);
            free(cpupath);
            return -1;
        }
        if (fclose(rapldomainfile) != 0) {
            PyErr_SetFromErrno(PyExc_IOError);
            free(cpupath);
            return -1;
        }
        // Read event scale
        FILE* rapldomainscalefile;
        char* scalepath = NULL;
        if (asprintf(&scalepath, "%s.scale", cpupath) == -1) {
            PyErr_SetFromErrno(PyExc_MemoryError);
            free(cpupath);
            return -1;
        }
        if ((rapldomainscalefile = fopen(scalepath, "r"))== NULL) {
            PyErr_SetFromErrno(PyExc_IOError);
            free(cpupath);
            free(scalepath);
            return -1;
        }
        if ( fscanf(rapldomainscalefile, "%lf", &self->config[i].scale) == EOF) {
            PyErr_SetFromErrno(PyExc_IOError);
            free(cpupath);
            free(scalepath);
            return -1;
        }
        if (fclose(rapldomainscalefile) != 0) {
            PyErr_SetFromErrno(PyExc_IOError);
            free(cpupath);
            free(scalepath);
            return -1;
        }
        free(scalepath);

        // Read event units
        FILE* rapldomainunitfile;
        char* unitpath = NULL;
        if (asprintf(&unitpath, "%s.unit", cpupath) == -1) {
            PyErr_SetFromErrno(PyExc_MemoryError);
            free(cpupath);
            return -1;
        }
        if ((rapldomainunitfile = fopen(unitpath, "r"))== NULL) {
            PyErr_SetFromErrno(PyExc_IOError);
            free(cpupath);
            free(unitpath);
            return -1;
        }
        char units[10];
        if ( fscanf(rapldomainunitfile, "%10s", units) == EOF) {
            PyErr_SetFromErrno(PyExc_IOError);
            free(cpupath);
            free(unitpath);
            return -1;
        }
        if (!strcmp(units,"Joules"))
        {
            self->config[i].units = 1;
        }
        if (fclose(rapldomainunitfile) != 0) {
            PyErr_SetFromErrno(PyExc_IOError);
            free(cpupath);
            free(unitpath);
            return -1;
        }
        free(unitpath);
        free(cpupath);
    }
    return 0;
}

static PyMemberDef Perf_members[] = {
    {"perf_paranoia_level", T_INT, offsetof(PerfObject, perf_paranoia_level), 0,
     "Paranoia level of perf on this system"},
    {"max_package_id", T_INT, offsetof(PerfObject, max_package_id), 0,
     "Highest package id on this system"},
    {"power_event_type", T_INT, offsetof(PerfObject, power_event_type), 0,
     "Perf event type for power events"},
    {NULL}  /* Sentinel */
};

static PyMethodDef Perf_methods[] = {
    {"start", (PyCFunction)perf_start, METH_NOARGS, "Start prof."},
    {"stop", (PyCFunction)perf_stop, METH_NOARGS, "Stop prof."},
    {"delta", (PyCFunction)perf_delta, METH_VARARGS, "get delta."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static PyTypeObject PerfType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "perf.Perf",
    .tp_doc = PyDoc_STR("Perf objects"),
    .tp_basicsize = sizeof(PerfObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = Perf_new,
    .tp_init = (initproc) Perf_init,
    .tp_dealloc = (destructor) Perf_dealloc,
    .tp_members = Perf_members,
    .tp_methods = Perf_methods,
};

PyMODINIT_FUNC PyInit_perf()
{
    PyObject *m;

    if (PyType_Ready(&PerfType) < 0)
        return NULL;

    m = PyModule_Create(&perfmodule);
    if (m == NULL)
        return NULL;

    Py_INCREF(&PerfType);
    if (PyModule_AddObject(m, "Perf", (PyObject *) &PerfType) < 0) {
        Py_DECREF(&PerfType);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}

static PyObject *
perf_start(PerfObject *self, PyObject *args)
{
    //long event_id = PyLong_AsLong(self)
    struct perf_event_attr attr;
    memset(&attr, 0, sizeof(struct perf_event_attr));
    attr.type = self->power_event_type;
    for (int package_id=0; package_id <= self->max_package_id; package_id++) {
        for (int perf_domain_i = 0; perf_domain_i < self->n_rapl_domains; perf_domain_i++) {
            if (self->config[perf_domain_i].event_id == 0) { // No event configured for this type
                continue;
            }
            attr.config = self->config[perf_domain_i].event_id;
            if ((self->perf_fd[package_id][perf_domain_i] = perf_event_open(&attr, -1, self->pack_cpu_id[package_id], -1, 0)) < 0)
            {
                PyErr_SetFromErrno(PyExc_IOError);
                return NULL;
            }
        }
    }
    self->last_energy = 0.0f;
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
perf_stop(PerfObject *self, PyObject *args)
{
    for (int package_id=0; package_id <= self->max_package_id; package_id++) {
        for (int perf_domain_i = 0; perf_domain_i < self->n_rapl_domains; perf_domain_i++) {
            // Skip unopened domains
            if (self->config[perf_domain_i].event_id == 0)
                continue;
            close(self->perf_fd[package_id][perf_domain_i]);
            self->perf_fd[package_id][perf_domain_i] = -1;
        }
    }
    Py_INCREF(Py_None);
    return Py_None;
}

static double read_energy(PerfObject* self)
{
    long long counter_value = 0;
    double calc_value = 0.0f;
    for (int package_id=0; package_id <= self->max_package_id; package_id++) {
        for (int perf_domain_i = 0; perf_domain_i < self->n_rapl_domains; perf_domain_i++) {
            // Skip unopened domains
            if (self->config[perf_domain_i].event_id == 0) {
                continue;
            }
            if (self->perf_fd[package_id][perf_domain_i] == -1) {
                PyErr_SetString(PyExc_Exception, "Delta on stopped hardware");
                return -1;
            }
            if (read(self->perf_fd[package_id][perf_domain_i], &counter_value, 8) == -1) {
                PyErr_SetFromErrno(PyExc_IOError);
                return -1;
            }

            calc_value += self->config[perf_domain_i].scale * (double)counter_value;
        }
    }
    return calc_value;
}

static PyObject*
perf_delta(PerfObject* self, PyObject* args)
{
    // Parse arguments
    double duration;
    if(!PyArg_ParseTuple(args, "d", &duration)) {
        return NULL;
    }
    double reading = read_energy(self);
    if (reading < 0) {
        return NULL;
    }

    PyObject* fromlist = PyTuple_Pack(2, PyUnicode_FromString("Energy"), PyUnicode_FromString("Power"));
    PyObject* imported = PyImport_ImportModuleEx("codecarbon.core.units",NULL,NULL,fromlist);
    if (!imported) {
        return NULL;
    }
    PyObject* energy_constructor = PyObject_GetAttrString(imported, "Energy");

    // energy in joules / duration in seconds = W
    // /1000 = kW
    //double power = (reading - self->last_energy) / (duration*1000);
    PyObject* energyfloat = PyFloat_FromDouble((reading-self->last_energy)/3600000);
    self->last_energy = reading;
    PyObject* result = PyObject_Call(energy_constructor,PyTuple_Pack(1,energyfloat),NULL);
    Py_INCREF(result);

    Py_DECREF(fromlist);
    Py_DECREF(imported);
    Py_DECREF(energyfloat);
    Py_DECREF(energy_constructor);
    return result;
}
