import React, { useState } from "react";

interface ModalProps<T, U> {
    isOpen: boolean;
    onClose: () => void;
    onSave: (data: T) => Promise<U>;
    initialData: T;
    initialSavedData: U;
    renderForm: (
        data: T,
        setData: React.Dispatch<React.SetStateAction<T>>,
    ) => React.ReactNode;
    renderSavedData: (
        data: U,
        setSavedData: React.Dispatch<React.SetStateAction<U>>,
    ) => React.ReactNode;
}

// This is a generic modal component that can be used to create any kind of modal that have a form and a saved data display.
// It takes in the following props:
// - isOpen: A boolean that determines if the modal is open or not.
// - onClose: A function that is called when the modal is closed.
// - onSave: A function that takes in the form data and returns a promise that resolves to the saved data.
// - initialData: The initial form data.
// - initialSavedData: The initial saved data.
// - renderForm: A function that takes in the form data and a function to set the form data and returns the form JSX.
// - renderSavedData: A function that takes in the saved data and a function to set the saved data and returns the saved data JSX.
const GeneralModal = <T, U>({
    isOpen,
    onClose,
    onSave,
    initialData,
    initialSavedData,
    renderForm,
    renderSavedData,
}: ModalProps<T, U>) => {
    const [data, setData] = useState<T>(initialData);
    const [isSavedDataDisplayed, setIsSavedDataDisplayed] = useState(false);
    const [savedData, setSavedData] = useState<U>(initialSavedData);

    const handleSave = async () => {
        const response = await onSave(data);
        setSavedData({ ...initialSavedData, ...response });
        setIsSavedDataDisplayed(true);
    };

    const handleClickOutside = (event: React.MouseEvent<HTMLDivElement>) => {
        if (event.target === event.currentTarget) {
            setIsSavedDataDisplayed(false);
            setData(initialData);
            setSavedData(initialSavedData);
            onClose();
        }
    };

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 flex items-center justify-center z-50 bg-primary/10"
            onClick={handleClickOutside}
        >
            <div className="rounded shadow-lg bg-background min-w-[664px] z-60 p-8">
                {!isSavedDataDisplayed ? (
                    <>
                        {renderForm(data, setData)}
                        <div className="flex justify-center">
                            <button
                                onClick={handleSave}
                                className="mt-4 px-4 py-2 rounded bg-primary text-primary-foreground"
                            >
                                Save
                            </button>
                        </div>
                    </>
                ) : (
                    <>
                        <div className="saved-data-display">
                            {renderSavedData(savedData, setSavedData)}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default GeneralModal;
