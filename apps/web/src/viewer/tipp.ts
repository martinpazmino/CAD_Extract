import * as BUI from "@thatopen/ui";

/** Tooltip fuer bim-button: BUI 3.4 erwartet <bim-tooltip> im Knopf (tooltip-title ist veraltet). */
export const tipp = (titel: string, text?: string) =>
  BUI.html`<bim-tooltip><strong>${titel}</strong>${text ? BUI.html`<br>${text}` : ""}</bim-tooltip>`;
