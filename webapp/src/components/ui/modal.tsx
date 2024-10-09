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
            className="fixed inset-0 flex items-center justify-center z-50"
            onClick={handleClickOutside}
        >
            <div className="p-4 rounded shadow-lg bg-secondary">
                {!isSavedDataDisplayed ? (
                    <>
                        {renderForm(data, setData)}
                        <button
                            onClick={handleSave}
                            className="mt-4 px-4 py-2 rounded bg-primary text-primary-foreground"
                        >
                            Save
                        </button>
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
