import React from "react";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: string;
  color?: "indigo" | "cyan" | "emerald" | "amber" | "rose";
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color = "indigo",
}) => {
  let iconBg = "rgba(99, 102, 241, 0.15)";
  let iconColor = "#818cf8";
  let borderGlow = "rgba(99, 102, 241, 0.1)";

  if (color === "cyan") {
    iconBg = "rgba(6, 182, 212, 0.15)";
    iconColor = "#22d3ee";
    borderGlow = "rgba(6, 182, 212, 0.1)";
  } else if (color === "emerald") {
    iconBg = "rgba(16, 185, 129, 0.15)";
    iconColor = "#34d399";
    borderGlow = "rgba(16, 185, 129, 0.1)";
  } else if (color === "amber") {
    iconBg = "rgba(245, 158, 11, 0.15)";
    iconColor = "#fbbf24";
    borderGlow = "rgba(245, 158, 11, 0.1)";
  } else if (color === "rose") {
    iconBg = "rgba(244, 63, 94, 0.15)";
    iconColor = "#fb7185";
    borderGlow = "rgba(244, 63, 94, 0.1)";
  }

  return (
    <div
      className="glass-card"
      style={{
        padding: "24px",
        borderColor: borderGlow,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        minHeight: "140px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-secondary)" }}>
          {title}
        </span>
        <div
          style={{
            width: 42,
            height: 42,
            borderRadius: 10,
            backgroundColor: iconBg,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: iconColor,
          }}
        >
          <Icon size={22} />
        </div>
      </div>

      <div style={{ marginTop: "14px" }}>
        <div style={{ fontSize: "2rem", fontWeight: 800, color: "#ffffff", lineHeight: 1 }}>
          {value}
        </div>
        {(subtitle || trend) && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              marginTop: "8px",
              fontSize: "0.8rem",
              color: "var(--text-muted)",
            }}
          >
            {trend && (
              <span
                style={{
                  color: trend.startsWith("+") ? "var(--accent-emerald)" : "var(--accent-rose)",
                  fontWeight: 600,
                }}
              >
                {trend}
              </span>
            )}
            {subtitle && <span>{subtitle}</span>}
          </div>
        )}
      </div>
    </div>
  );
};
