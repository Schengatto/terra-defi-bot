/**
 * Return the object Date forcing UTC as timezone.
 * @param date
 */
export function createDateAsUtc(date: Date) {
    return new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), date.getMinutes(), date.getSeconds()));
}
