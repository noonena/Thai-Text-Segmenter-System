"use client";
import { useState } from "react";
import { X } from "lucide-react";

type Props = {
    onClose: () => void;
    onApply: (settings: { tag: "span" | "div"; cssClass: string }) => void;
};

export default function SettingPage({ onClose, onApply }: Props) {
    // draft (user editing)
    const [draftTag, setDraftTag] = useState<"span" | "div">("span");
    const [draftClass, setDraftClass] = useState("");
    const [openTag, setOpenTag] = useState(false);

    // applied (used by preview)
    const [tag, setTag] = useState<"span" | "div">("span");
    const [cssClass, setCssClass] = useState("");

    const applySettings = () => {
        setTag(draftTag);
        setCssClass(draftClass.trim());
        onApply({ tag: draftTag, cssClass: draftClass.trim() });
        onClose();
    };

    const handleCancel = () => {
        // Reset draft values to applied values
        setDraftTag(tag);
        setDraftClass(cssClass);
        onClose();
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter") {
            applySettings();
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* backdrop */}
            <div
                className="absolute inset-0 bg-black/40"
                onClick={handleCancel}
            />

            {/* modal */}
            <div className="relative w-[720px] max-w-[92%] rounded-xl bg-white shadow-2xl overflow-hidden">
                {/* header */}
                <div className="flex items-center justify-between px-6 py-4 bg-black text-white">
                    <h2 className="text-lg font-semibold">Output Settings</h2>
                    <button onClick={handleCancel}>
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* body */}
                <div className="p-6 space-y-6">
                    {/* controls */}
                    <div className="grid grid-cols-2 gap-4">
                        {/* dropdown */}
                        <div>
                            <div className="relative">
                                <label className="block text-xs font-medium text-gray-500 mb-1">
                                    HTML Tag Type
                                </label>

                                {/* Trigger */}
                                <button
                                    onClick={() => setOpenTag((v) => !v)}
                                    className="w-full h-10 rounded-md bg-gray-100 px-3 text-sm flex items-center justify-between border border-transparent hover:bg-gray-200 focus:outline-none focus:border-black"
                                >
                                    <span>
                                        {draftTag === "span" ? "<span> · inline" : "<div> · block"}
                                    </span>
                                    <span className="text-gray-400 text-xs">▾</span>
                                </button>

                                {/* Dropdown */}
                                {openTag && (
                                    <div className="absolute mt-1 w-full z-50 rounded-lg bg-white border border-gray-200 shadow-lg p-1">
                                        <DropdownItem
                                            active={draftTag === "span"}
                                            label="<span> · inline"
                                            onClick={() => {
                                                setDraftTag("span");
                                                setTag("span");
                                                setDraftClass("");
                                                setCssClass("");
                                                setOpenTag(false);
                                            }}
                                        />
                                        <DropdownItem
                                            active={draftTag === "div"}
                                            label="<div> · block"
                                            onClick={() => {
                                                setDraftTag("div");
                                                setTag("div");
                                                setDraftClass("");
                                                setCssClass("");
                                                setOpenTag(false);
                                            }}
                                        />
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* input */}
                        <div>
                            <label className="block text-xs font-medium text-gray-500 mb-1">
                                CSS class <span className="text-gray-400">(optional)</span>
                            </label>
                            <input
                                value={draftClass}
                                onChange={(e) => {
                                    const value = e.target.value;
                                    setDraftClass(value);
                                    setCssClass(value.trim());
                                }}
                                onKeyDown={handleKeyDown}
                                placeholder="eg. no-wrap"
                                className="w-full h-10 rounded-md bg-gray-100 px-3 text-sm border border-transparent focus:bg-white focus:border-black focus:outline-none"
                            />
                        </div>
                    </div>

                    {/* preview */}
                    <div>
                        <label className="block text-xs font-medium text-gray-500 mb-2">
                            Preview
                        </label>
                        <pre className="bg-black text-gray-100 rounded-lg p-4 text-xs leading-relaxed h-[180px] overflow-auto">
                            {['ผม', 'ชอบ', 'กิน', 'ข้าวผัด', 'อร่อย'].map((word, i) =>
                                `${i > 0 ? '<wbr>' : ''}<${tag}${cssClass ? ` class="${cssClass}"` : ''}>${word}</${tag}>`
                            ).join('\n')}
                        </pre>
                    </div>

                    {/* actions */}
                    <div className="flex justify-end gap-3">
                        <button
                            onClick={handleCancel}
                            className="px-4 py-2 text-sm rounded-md border border-gray-300 text-gray-700"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={applySettings}
                            className="px-4 py-2 text-sm rounded-md bg-black text-white"
                        >
                            Apply
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function DropdownItem({
    label,
    active,
    onClick,
}: {
    label: string;
    active: boolean;
    onClick: () => void;
}) {
    return (
        <button
            onClick={onClick}
            className={`w-full px-3 py-2 text-sm text-left rounded-md flex items-center justify-between ${
                active
                    ? "bg-gray-100 font-medium text-gray-900"
                    : "hover:bg-gray-100 text-gray-700"
            }`}
        >
            {label}
            {active && <span className="text-xs text-gray-400">✓</span>}
        </button>
    );
}