import {Dictionary} from "@/utils/object";

const cancelProperty = "__CANCEL__";

/**
 * Return true if the event is related to a cancelled http request.
 * @param event
 */
export function isCancelEvent(event: object): boolean {
    const proto = Object.getPrototypeOf(event);
    return proto[cancelProperty];
}

export function getItemStringValue(item: any) : string {
    return item instanceof Date
        ? item.toUTCString()
        : String(item);
}

/**
 * Return the query string value of the filter value provided as input.
 * @param filterValue
 */
export function toQueryStringValue(filterValue: any): string {
    return  Array.isArray(filterValue)
        ? String(filterValue.map(i => getItemStringValue(i)))
        : getItemStringValue(filterValue);
}

/**
 * Return query params string. If the baseUrl is provided then this method returns the url
 * of the request comprehensive of the query params provided as input.
 * @param params
 * @param baseUrl
 */
export function buildUrlQueryParams(params: Dictionary<string | number | boolean | Date | (string | number | Date)[] | null | undefined>, baseUrl = ""): string {
    return Object.keys(params)
        .filter(k => params[k] !== null && params[k] !== undefined && params[k] !== "" )
        .reduce((acc, cur, index) => (acc.concat(`${index === 0 ? "?" : "&"}${cur}=${encodeURIComponent(toQueryStringValue(params[cur]!))}`)), `${baseUrl}`);
}


/**
 * Return the baseUrl without the query parameters from the requestUrl provided as input.
 * @param requestUrl
 */
export function getUrlWithoutQueryParams(requestUrl: string): string {
    return requestUrl.indexOf("?") > -1 ? requestUrl.substr(0, requestUrl.indexOf("?")) : requestUrl;
}


/**
 * Creates a temporary anchor and triggers the download from URL.
 * @param fileURL
 * @param fileName
 */
export function downloadFileFromUrl(fileURL: string, fileName: string): void {
    const fileLink = document.createElement("a");
    fileLink.href = fileURL;
    fileLink.target = "_blank";
    fileLink.setAttribute("download", fileName);
    document.body.appendChild(fileLink);
    fileLink.click();
    fileLink.remove();
}

/**
 * Creates a fileURL from Blob and triggers downloadFileFromUrl.
 * @param data
 * @param fileName
 */
export function downloadFileFromBlob(data: Blob, fileName: string): void {
    const fileURL = URL.createObjectURL(data);
    downloadFileFromUrl(fileURL, fileName);
}
