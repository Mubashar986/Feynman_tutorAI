import "@testing-library/jest-dom";
import { configure } from "@testing-library/dom";
import { afterEach } from "vitest";

// Configure testing library to not fail on aria-hidden during modal portals
configure({ defaultHidden: true });

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

// Clean up Radix/Vaul scroll and aria-hidden locks between tests
afterEach(() => {
  if (typeof document !== "undefined") {
    document.body.removeAttribute("data-scroll-locked");
    document.body.style.pointerEvents = "";
    document.querySelectorAll("[data-aria-hidden]").forEach((el) => {
      el.removeAttribute("data-aria-hidden");
      el.removeAttribute("aria-hidden");
    });
  }
});

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
