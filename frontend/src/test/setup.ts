import "@testing-library/jest-dom";

// Mock matchMedia for components relying on dark-mode / media queries
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Mock ResizeObserver for Radix UI / Vaul primitives
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock scrollIntoView for JSDOM
if (typeof window !== "undefined") {
  window.HTMLElement.prototype.scrollIntoView = function () {};
}

// Safe getComputedStyle wrapper for JSDOM
const originalGetComputedStyle = window.getComputedStyle;
window.getComputedStyle = (element, pseudoElt) => {
  try {
    const res = originalGetComputedStyle(element, pseudoElt);
    if (!res) throw new Error("Null style");
    return res;
  } catch {
    return {
      getPropertyValue: () => "",
      display: "block",
      visibility: "visible",
      opacity: "1",
    } as unknown as CSSStyleDeclaration;
  }
};
