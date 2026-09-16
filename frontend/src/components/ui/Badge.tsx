import React from "react";

interface BadgeProps {
  status?: string | null;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ status, className = "" }) => {
  if (!status) return null;

  const s = status.toUpperCase();

  let badgeClass = "badge-closed";
  if (s === "NEW") {
    badgeClass = "badge-new";
  } else if (s === "OPEN" || s === "ACTIVE" || s === "INSERTED") {
    badgeClass = "badge-open";
  } else if (s === "NEEDS_REVIEW" || s === "PENDING") {
    badgeClass = "badge-needs-review";
  } else if (s === "UPDATED" || s === "RUNNING") {
    badgeClass = "badge-updated";
  } else if (s === "INACTIVE" || s === "CANCELLED" || s === "FAILED" || s === "EXTRACTION_FAILED") {
    badgeClass = "badge-inactive";
  }

  return (
    <span className={`badge ${badgeClass} ${className}`}>
      {status}
    </span>
  );
};
