import {EnumDropdownItem} from "@/models/common.model";

export function getEnumDropdown(e: { [s: string]: string | number }): EnumDropdownItem[] {
    return Object.entries(e).map(([key, value]) => ({
        id: value,
        name: key
    }));
}