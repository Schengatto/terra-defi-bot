// enable json date parser
// source code on https://github.com/RickStrahl/json.date-extensions

import {createDateAsUtc} from "@/utils/date";

export class CustomJSONParser {
    private static ReISO = new RegExp(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2}(?:\.{0,1}\d*))(?:Z|(\+|-)([\d|:]*))?$/);

    public static parse(json: string, transformChain?: (key: any, value: any) => any): any {
        try {
            return JSON.parse(json, CustomJSONParser.GetParser(false, transformChain));
        } catch (e) {
            throw new Error("JSON content could not be parsed");
        }
    }

    public static parseForcingUtcDates(json: string, transformChain?: (key: any, value: any) => any): any {
        try {
            return JSON.parse(json, CustomJSONParser.GetParser(true, transformChain));
        } catch (e) {
            throw new Error("JSON content could not be parsed");
        }
    }

    private static GetParser(forceUtc: boolean, transformChain?: (key: any, value: any) => any) {
        return (key: any, value: any) => {
            let parsedValue = value;

            if (CustomJSONParser.isDate(value)) {
                parsedValue = forceUtc
                    ? createDateAsUtc(new Date(value))
                    : new Date(value);
            }

            return CustomJSONParser.isTransformChainValid(transformChain)
                ? transformChain!(key, parsedValue)
                : parsedValue;
        };
    }

    private static isDate(value: any): boolean {
        return value instanceof Date || (typeof value === "string" && !!CustomJSONParser.ReISO.exec(value));
    }

    private static isTransformChainValid(transformChain: ((key: any, value: any) => any) | undefined): boolean {
        return !!transformChain && typeof (transformChain) === "function";
    }
}
