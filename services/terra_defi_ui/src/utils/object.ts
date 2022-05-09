import {Decimal} from "@/models/decimal";

export type Dictionary<T> = Record<string, T>;

/**
 * Return true if the object provided as input is not null and not undefined.
 * @param object
 */
export function isNullOrUndefined(object: any): boolean {
    return (object === null || object === undefined);
}

/**
 * Return true if the object provided as input is not null and not undefined.
 * @param object
 */
export function isNotNullOrUndefined(object: any): boolean {
    return (!(object === null || object === undefined));
}

/**
 * Return an array of string with oll the keys of the object provided as input.
 * @param obj
 */
export function getObjectKeys(obj: Dictionary<any>): Array<string> {
    return isNotNullOrUndefined(obj) ? Array.from(Object.keys(obj)) : [];
}

/**
 * Return the object provided as argument without the property with value null.
 * @param obj
 */
export function removeNullProperties<TInput extends Dictionary<any>, TOutput extends Dictionary<any> = TInput>(obj: TInput): TOutput {
    return Object.fromEntries(Object.entries(obj).filter(([_, v]) => v !== null)) as TOutput;
}

/**
 * Return the object provided as argument without the property with value null.
 * @param obj
 */
export function isObject(obj: any): boolean {
    return obj !== null
        && !Array.isArray(obj)
        && typeof obj === "object";
}

/**
 * Deep copy of the object provided as input.
 * TODO: This isn't a scalable solution. We should find a better alternative that cover all cases.
 * @param obj
 */
export function clonePlainObject(obj: any): any {
    if (isNullOrUndefined(obj)) {
        return null;
    }
    let copy;

    // Handle the 3 simple types, and null or undefined
    if (null == obj || "object" != typeof obj) return obj;

    // Handle Date
    if (obj instanceof Date) {
        copy = new Date();
        copy.setTime(obj.getTime());
        return copy;
    }

    // Handle Array
    if (obj instanceof Array) {
        copy = [];
        for (let i = 0, len = obj.length; i < len; i++) {
            copy[i] = clonePlainObject(obj[i]);
        }
        return copy;
    }

    // Handle Decimal
    if (obj instanceof Decimal) {
        copy = new Decimal(obj.value, obj.precision);
        return copy;
    }

    // Handle Object
    if (obj instanceof Object) {
        return getObjectKeys(obj)
            // eslint-disable-next-line no-prototype-builtins
            .filter(k => obj.hasOwnProperty(k))
            .reduce((acc, k) => {
                // @ts-ignore
                acc[k] = clonePlainObject(obj[k]);
                return acc;
            }, {});
    }
    throw new Error("Unable to copy obj! Its type isn't supported.");
}
