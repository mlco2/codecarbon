import { IProjectToken } from "@/types/project";
import React, { useState } from "react";
import { ClipboardCopy } from "lucide-react";

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (name: string) => Promise<IProjectToken>;
}

const Modal: React.FC<ModalProps> = ({ isOpen, onClose, onSave }) => {
    const [name, setName] = useState("");
    const [isTokenDisplayed, setIsTokenDisplayed] = useState(false);
    const [token, setToken] = useState("");

    const handleSave = async () => {
        if (!name || name === "") return;
        const projectToken: IProjectToken = await onSave(name);
        console.log(projectToken);
        setIsTokenDisplayed(true);
        setToken(projectToken.token);
    };
    const handleClickOutside = (event: React.MouseEvent<HTMLDivElement>) => {
        if (event.target === event.currentTarget) {
            handleClose();
        }
    };
    const handleClose = () => {
        setName("");
        setIsTokenDisplayed(false);
        onClose();
    };
    const handleCopy = () => {
        navigator.clipboard
            .writeText(token)
            .then(() => {
                alert("Token copied to clipboard");
            })
            .catch((err) => {
                console.error("Failed to copy token: ", err);
            });
    };

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 flex items-center justify-center z-50"
            onClick={handleClickOutside}
        >
            <div className="p-4 rounded shadow-lg bg-secondary">
                {!isTokenDisplayed ? (
                    <>
                        <h2 className="text-xl font-bold mb-4">
                            Create new token
                        </h2>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="border p-2 w-full"
                            placeholder="Token Name"
                        />
                        <button
                            onClick={handleSave}
                            className="mt-4 px-4 py-2 rounded bg-primary text-primary-foreground"
                        >
                            Save
                        </button>
                    </>
                ) : (
                    <>
                        <h2 className="text-xl font-bold mb-4">
                            Token Created
                        </h2>
                        <p className="text-l mb-4">
                            The following token has been generated:
                        </p>
                        <div className="bg-muted flex items-center p-2 rounded ">
                            <pre className="m-0">
                                <code>{token}</code>
                            </pre>
                            <button
                                onClick={handleCopy}
                                className="ml-2 px-4 py-2 rounded text-gray-500 hover:text-gray-700"
                            >
                                <ClipboardCopy />
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default Modal;
