// @vitest-environment jsdom
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { App } from "./App";

interface MockTreeOptions {
  paths: readonly string[];
  onSelectionChange?: (paths: readonly string[]) => void;
}

vi.mock("@pierre/diffs/react", () => ({
  MultiFileDiff: ({ newFile }: { newFile: { name: string } }) => (
    <div data-testid="rendered-diff">{newFile.name}</div>
  ),
}));

vi.mock("@pierre/trees/react", () => ({
  useFileTree: (options: MockTreeOptions) => ({ model: options }),
  FileTree: ({ model }: { model: MockTreeOptions }) => (
    <nav>
      {model.paths.map((path) => (
        <button key={path} onClick={() => model.onSelectionChange?.([path])}>
          {path}
        </button>
      ))}
    </nav>
  ),
}));

describe("review workbench navigation", () => {
  it("shows the diff selected in the path tree", () => {
    render(<App />);
    expect(screen.getByTestId("rendered-diff").textContent).toBe("src/users.py");

    fireEvent.click(screen.getByRole("button", { name: "src/members.py" }));

    expect(screen.getByTestId("rendered-diff").textContent).toBe("src/members.py");
    expect(screen.getByRole("heading", { name: "Reviewing src/members.py" })).toBeTruthy();
  });
});