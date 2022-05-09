/* eslint-disable @typescript-eslint/no-empty-function */

import Session from "@/utils/session";

const host = process.env.VUE_APP_API_SERVICE_HOST;
const port = process.env.VUE_APP_API_SERVICE_PORT;

import axios, {AxiosInstance, AxiosRequestConfig, CancelTokenSource} from "axios";
import {buildUrlQueryParams, getUrlWithoutQueryParams, isCancelEvent} from "@/utils/http";
import {AuthUtils} from "@/utils/auth-utils";
import {Dictionary} from "@/utils/object";

export interface HttpGetOptions {
    hasCustomErrorHandler?: boolean;
}

export interface HttpPostOptions {
    contentType?: string;
    hasCustomErrorHandler?: boolean;
}

export interface GetFileResponse {
    fileName: string;
    fileData: Blob;
}

type PendingRequests = Map<string, CancelTokenSource>;

export class HttpService {
    axios: AxiosInstance;
    cancelTokenSource?: CancelTokenSource;

    constructor() {
        this.cancelTokenSource = axios.CancelToken.source();
        this.axios = axios.create({
            cancelToken: this.cancelTokenSource.token
        });

        const pendingRequests: PendingRequests = new Map<string, CancelTokenSource>();

        window.addEventListener("unhandledrejection", function (event) {
            if (isCancelEvent(event.reason)) {
                event.preventDefault();
            }
        });

        this.axios.interceptors.request.use(function (config) {
            const tokenSource = axios.CancelToken.source();

            if (config.method === "get" && config.url) {
                const requestUrl = getUrlWithoutQueryParams(config.url);
                const previousRequestCancelTokenSource = pendingRequests.get(requestUrl);
                if (previousRequestCancelTokenSource) {
                    previousRequestCancelTokenSource.cancel();
                }
                pendingRequests.set(requestUrl, tokenSource);
            }
            // TODO: remove the forcing UTC when the BE is be able to handle Timezones
            if (config.headers && config.headers["Content-Type"] !== "multipart/form-data") {
                config.data = HttpService.parseForcingUtcDates(config.data);
            }
            return {...config, data: config.data, cancelToken: tokenSource.token};

        }, function (error) {
            alert(`😖 ${error.message || JSON.stringify(error)}`);
            return Promise.reject(error);
        });

        this.axios.interceptors.response.use(
            (res) => {
                if (res.config.url) {
                    HttpService.deletePendingRequest(res.config.url, pendingRequests);
                }

                if (res.config.responseType === "blob") {
                    return res;
                }

                return HttpService.parseResponseDates(res);
            },
            (error) => {
                if (isCancelEvent(error)) {
                    return Promise.reject(error);
                }

                if (error.config && error.config.url) {
                    HttpService.deletePendingRequest(error.config.url, pendingRequests);
                }

                let requestHeaders = [];
                if (error) {
                    requestHeaders = error.request.requestHeaders || error.config.headers;
                }
                

                // not authorized, move to login page
                if (error.response && [401, 403].includes(error.response.status)) {
                    window.open(location.origin + "/account/signout", "_self");
                    return;
                }
                // handle not found
                if (error.response && error.response.status == 404) {
                    return;
                }

                // handle bad request
                if (error.response && [400, 415].includes(error.response.status)) {

                    alert(error.response.data);
                    return Promise.reject(error);
                }
                console.error(error);

                return Promise.reject(error);
            }
        );
    }

    static async getBaseConfig(): Promise<AxiosRequestConfig> {
        return {
            headers: {
                ...AuthUtils.authorizedHeader()
            }
        };
    }

    static deletePendingRequest(requestUrl: string, pendingRequests: Map<string, CancelTokenSource>): void {
        pendingRequests.delete(getUrlWithoutQueryParams(requestUrl));
    }

    // TODO create an interface for all those services which need the init method
    init(): void {
        this.axios.defaults.baseURL = `${host}:${port}`
        this.axios.defaults.headers.common["Client-Session-Id"] = Session.Id;
    }

    setLanguageHeader(lang: string): void {
        this.axios.defaults.headers.common["Accept-Language"] = lang;
    }

    cancelPendingRequests(): void {
        // cancel all pending requests
        if (this.cancelTokenSource) {
            this.cancelTokenSource.cancel();
        }
        // create new cancellation token source
        this.cancelTokenSource = axios.CancelToken.source();
    }

    static parseResponseDates(response: any): any {
        return response;
    }

    static parseForcingUtcDates(requestData: any): any {
        return requestData;
    }

    isFailResponse(data: any): boolean {
        return typeof data === "object"
            && "code" in data
            && "message" in data;
    }

    async get<T>(url: string, parameters?: Dictionary<string | number | boolean | Date | (string | number | Date)[] | null | undefined>, options?: HttpGetOptions): Promise<T> {
        const config = await HttpService.getBaseConfig();
        if (parameters) {
            url = `${url}${buildUrlQueryParams(parameters)}`;
        }
        if (config.headers) {
            config.headers["Content-Type"] = "application/json";
        }
        return this.axios.get<T>(url, config).then(res => res.data);
    }

    async getFile(url: string, parameters?: Dictionary<string | number | (string | number)[] | null | undefined>): Promise<GetFileResponse> {
        const config = await HttpService.getBaseConfig();
        if (parameters) {
            url = `${url}${buildUrlQueryParams(parameters)}`;
        }

        const response = await this.axios.get(url, {
            ...config,
            responseType: "blob"
        });

        return {
            fileName: this.getFileNameFromContentDispositionHeader(response.headers["content-disposition"] || "") || "untitled-file",
            fileData: new Blob([response.data], {type: response.headers["content-type"]})
        };
    }

    async post<TRequest, TResponse = void>(url: string, data: TRequest, options?: HttpPostOptions): Promise<TResponse> {
        const config = await HttpService.getBaseConfig();

        if (config.headers) {
            config.headers["Content-Type"] = options ? options.contentType : "application/json";
        }
        return this.axios.post<TResponse>(url, data, config).then(res => res.data);
    }

    private getFileNameFromContentDispositionHeader(header: string): string | null {
        if (header.startsWith("attachment")) {
            const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
            const matches = filenameRegex.exec(header);
            if (matches !== null && matches[1]) {
                return matches[1].replace(/['"]/g, "");
            }
        }

        return null;
    }
}

export default new HttpService();
