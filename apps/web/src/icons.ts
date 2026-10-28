// Icons offline: BUI (iconify-icon) holt jedes Icon sonst zur Laufzeit von api.iconify.design.
// scripts/vendor.mjs sammelt alle in src/ benutzten Namen aus den @iconify-json-Paketen.
import { addCollection, type IconifyJSON } from "iconify-icon";
import sammlungen from "./icons.gen.json";

for (const s of sammlungen as unknown as IconifyJSON[]) addCollection(s);
