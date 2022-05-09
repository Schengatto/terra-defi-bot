// Constraints:
// (Number.MIN_SAFE_INTEGER / 10^precision)) < value < (Number.MAX_SAFE_INTEGER / 10^precision))
export class Decimal {

    private readonly precisionValue: number;
    private readonly precisionMultiplier: number;
    private readonly decimalPlaces: number | null;
    private fixedValue: number;

    constructor(value: number, precision = 4, decimalPlaces: null | number = null) {
        this.precisionValue = precision;
        this.precisionMultiplier = Math.pow(10, this.precisionValue);
        this.decimalPlaces = decimalPlaces;
        this.fixedValue = this.sanitizeValue(value);
    }

    get isValid(): boolean {
        return isFinite(this.intFixedValue) && Number.isSafeInteger(this.intFixedValue);
    }

    get value(): number {
        return this.fixedValue;
    }

    private get intFixedValue(): number {
        return this.sanitizeValue(this.fixedValue * this.precisionMultiplier);
    }

    get precision(): number {
        return this.precisionValue;
    }

    toString(): string {
        return this.decimalPlaces !== null
            ? String(this.fixedValue.toFixed(this.decimalPlaces))
            : String(this.fixedValue);
    }

    toJSON(): number {
        return this.value;
    }

    add(value: number): this {
        this.fixedValue = (this.intFixedValue + this.sanitizeValue(value * this.precisionMultiplier)) / this.precisionMultiplier;
        return this;
    }

    sub(value: number): this {
        this.fixedValue = (this.intFixedValue - this.sanitizeValue(value * this.precisionMultiplier)) / this.precisionMultiplier;
        return this;
    }

    multiplyBy(value: number): this {
        this.fixedValue = this.sanitizeValue((this.intFixedValue * this.sanitizeValue(value)) / this.precisionMultiplier);
        return this;
    }

    divideBy(value: number): this {
        this.fixedValue = this.sanitizeValue((this.intFixedValue / this.sanitizeValue(value)) / this.precisionMultiplier);
        return this;
    }

    private sanitizeValue(value: number): number {
        return Number(value.toFixed(this.precisionValue));
    }
}
