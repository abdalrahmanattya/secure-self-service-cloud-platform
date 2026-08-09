import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CopyValue } from "./CopyValue";

afterEach(() => cleanup());

describe("CopyValue", () => {
  it("provides accessible feedback after copying successfully", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    render(<CopyValue value="proposal-hash" label="Content hash" />);

    await user.click(screen.getByRole("button", { name: "Copy Content hash" }));

    expect(writeText).toHaveBeenCalledWith("proposal-hash");
    expect(await screen.findByRole("status")).toHaveTextContent("Copied");
  });

  it.each([
    ["rejects", vi.fn().mockRejectedValue(new Error("denied"))],
    ["is unavailable", undefined],
  ])(
    "reports when the clipboard %s without an unhandled rejection",
    async (_state, writeText) => {
      const user = userEvent.setup();
      Object.defineProperty(navigator, "clipboard", {
        configurable: true,
        value: writeText ? { writeText } : undefined,
      });
      render(<CopyValue value="proposal-hash" />);

      await user.click(screen.getByRole("button", { name: "Copy value" }));

      expect(await screen.findByRole("status")).toHaveTextContent(
        "Copy failed",
      );
    },
  );
});
