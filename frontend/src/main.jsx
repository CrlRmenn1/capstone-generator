import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

// Wait briefly for the two typefaces before the first paint, so text doesn't reflow
// when they swap in. The fonts ship with the app, so this is usually instant; the
// timeout makes sure a slow device never waits long.
const fonts = ['400 16px "Source Serif 4 Variable"', '600 16px "Source Serif 4 Variable"', '400 16px "Instrument Sans Variable"'];
const fontsReady = Promise.race([
  Promise.all(fonts.map((f) => document.fonts?.load(f))).catch(() => {}),
  new Promise((resolve) => setTimeout(resolve, 900)),
]);

fontsReady.finally(() => {
  createRoot(document.getElementById("root")).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
});
