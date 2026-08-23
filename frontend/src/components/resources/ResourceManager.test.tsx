import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import React from "react";
import { ResourceManagerView } from "./ResourceManagerView";
import { DocumentGrid } from "./DocumentGrid";
import { DocumentChunkViewer } from "./DocumentChunkViewer";
import { SemanticSearchSandbox } from "./SemanticSearchSandbox";
import { MOCK_DOCUMENTS } from "@/api/documents";

// Mock KaTeX renderer for fast DOM assertions
vi.mock("@/components/common/LaTeXRenderer", () => ({
  LaTeXRenderer: ({ content }: { content: string }) => (
    <div data-testid="latex-content">{content}</div>
  ),
}));

describe("ResourceManagerView & Curriculum Resource Explorer (Task 3.4)", () => {
  it("renders document library with metrics banner and document cards", async () => {
    render(
      <ResourceManagerView
        examTemplateId="exam_alevel_01"
        userRole="admin"
      />
    );

    // Assert Header & Metrics
    expect(
      screen.getByText("Curriculum Library & Resource Manager")
    ).toBeInTheDocument();
    expect(screen.getByText("Total Documents")).toBeInTheDocument();
    expect(screen.getByText("Semantic Chunks")).toBeInTheDocument();
    expect(screen.getByText("Vector Status")).toBeInTheDocument();

    // Assert Document Cards rendered from mock
    await waitFor(() => {
      expect(
        screen.getByText("University Physics: Classical Mechanics & Vectors")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Principles of Geometric & Wave Optics")
      ).toBeInTheDocument();
    });
  });

  it("switches to Semantic Search Sandbox tab and executes vector search", async () => {
    render(
      <ResourceManagerView
        examTemplateId="exam_alevel_01"
        userRole="student"
      />
    );

    // Switch to Sandbox Tab
    const sandboxTabButton = screen.getByRole("button", {
      name: /Semantic Search Sandbox/i,
    });
    fireEvent.click(sandboxTabButton);

    expect(
      screen.getByText(/Semantic Vector Search & Provenance Sandbox/i)
    ).toBeInTheDocument();

    // Trigger Search Query
    const searchInput = screen.getByPlaceholderText(
      /Ask any syllabus concept/i
    );
    fireEvent.change(searchInput, {
      target: { value: "Kinematic velocity derivation" },
    });

    const retrieveButton = screen.getByRole("button", { name: /Retrieve/i });
    fireEvent.click(retrieveButton);

    // Assert Citation Cards Rendered
    await waitFor(() => {
      expect(
        screen.getByText(/Chapter 2 > Kinematics in One Dimension/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/94% Similarity/i)).toBeInTheDocument();
    });
  });

  it("opens and closes DocumentChunkViewer with KaTeX formula rendering", async () => {
    const handleClose = vi.fn();
    render(
      <DocumentChunkViewer
        document={MOCK_DOCUMENTS[0]}
        onClose={handleClose}
      />
    );

    expect(
      screen.getByText(MOCK_DOCUMENTS[0].title)
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(
        screen.getByText(/Average vs Instantaneous Velocity/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/The Torricelli Equation/i)).toBeInTheDocument();
    });

    // Close Inspector
    const closeBtn = screen.getByRole("button", { name: /Close Inspector/i });
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("opens and closes DocumentUploadModal for instructor/admin users", async () => {
    render(
      <ResourceManagerView
        examTemplateId="exam_alevel_01"
        userRole="admin"
      />
    );

    const uploadBtn = screen.getByRole("button", {
      name: /Upload Source Document/i,
    });
    fireEvent.click(uploadBtn);

    expect(screen.getByText("Upload Source Material")).toBeInTheDocument();
    expect(
      screen.getByText(/Drag and drop your file here/i)
    ).toBeInTheDocument();

    const cancelBtn = screen.getByRole("button", { name: /Cancel/i });
    fireEvent.click(cancelBtn);

    await waitFor(() => {
      expect(
        screen.queryByText("Upload Source Material")
      ).not.toBeInTheDocument();
    });
  });
});
