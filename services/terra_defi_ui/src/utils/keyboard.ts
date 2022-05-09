// TODO add better macos detection

// Checks if pressed key combination is copy
export function isCopyKey(event: KeyboardEvent): boolean {
    return (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "c";
}

// Checks if pressed key combination is cut
export function isCutKey(event: KeyboardEvent): boolean {
    return (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "x";
}

// Checks if pressed key combination is paste
export function isPasteKey(event: KeyboardEvent): boolean {
    return (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "v";
}

// Checks if pressed key combination is select all
export function isSelectAllKey(event: KeyboardEvent): boolean {
    return (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "a";
}

// Checks if pressed key combination is any clipboard event
export function isClipboardKey(event: KeyboardEvent): boolean {
    return isCopyKey(event) || isCutKey(event) || isPasteKey(event) || isSelectAllKey(event);
}
