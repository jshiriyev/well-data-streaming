const SUITE = {
    trail: {
        count: 3,
        gap: 0.05,
        array: [],
        get totalGap() {
            const count = Math.max(1, Math.floor(Number(this.count) || 1));
            const gap = Number.isFinite(this.gap) ? this.gap : 0;
            return gap * (count - 1);
        },
        get width() {
            const count = Math.max(1, Math.floor(Number(this.count) || 1));
            return (1 - this.totalGap) / count;
        },
    },
    topDepth: null,
    baseDepth: null,
    get range() {
        return [this.baseDepth, this.topDepth];
    },
    grid: {
        show: true,
        width: 1,
        color: "#000000",
        alpha: 0.1,
        get gridcolor() {
            const hex = this.color.replace("#", "");
            const r = parseInt(hex.slice(0, 2), 16);
            const g = parseInt(hex.slice(2, 4), 16);
            const b = parseInt(hex.slice(4, 6), 16);
            return `rgba(${r},${g},${b},${this.alpha})`;
        },
        minor: {
            show: true,
            width: 0.5,
            color: "#000000",
            alpha: 0.1,
            get gridcolor() {
                const hex = this.color.replace("#", "");
                const r = parseInt(hex.slice(0, 2), 16);
                const g = parseInt(hex.slice(2, 4), 16);
                const b = parseInt(hex.slice(4, 6), 16);
                return `rgba(${r},${g},${b},${this.alpha})`;
            },
        },
    },
    separator: {
        show: true,
        width: 1,
        color: "#000000",
        alpha: 1.0,
        get sepcolor() {
            const hex = this.color.replace("#", "");
            const r = parseInt(hex.slice(0, 2), 16);
            const g = parseInt(hex.slice(2, 4), 16);
            const b = parseInt(hex.slice(4, 6), 16);
            return `rgba(${r},${g},${b},${this.alpha})`;
        },
    },
};

const TRAIL = {
    xMin: 0,
    xMax: 100,
    get range() {
        return [this.xMin, this.xMax];
    },
    scale: "linear",
    major: 10,
    minor: 1,
    grid: {
        show: true,
        width: 1,
        color: "#000000",
        alpha: 0.1,
        get gridcolor() {
            const hex = this.color.replace("#", "");
            const r = parseInt(hex.slice(0, 2), 16);
            const g = parseInt(hex.slice(2, 4), 16);
            const b = parseInt(hex.slice(4, 6), 16);
            return `rgba(${r},${g},${b},${this.alpha})`;
        },
        minor: {
            show: true,
            width: 0.5,
            color: "#000000",
            alpha: 0.1,
            get gridcolor() {
                const hex = this.color.replace("#", "");
                const r = parseInt(hex.slice(0, 2), 16);
                const g = parseInt(hex.slice(2, 4), 16);
                const b = parseInt(hex.slice(4, 6), 16);
                return `rgba(${r},${g},${b},${this.alpha})`;
            },
        }
    },
    curves: new Set(),
}
