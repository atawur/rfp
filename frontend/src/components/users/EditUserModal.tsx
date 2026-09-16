"use client";

import React, { useState, useEffect } from "react";
import { Modal } from "@/components/ui/Modal";
import { userService } from "@/services/userService";
import { useToast } from "@/context/ToastContext";
import { User, UserUpdate } from "@/types";
import { Save, Loader2, Shield, Mail, User as UserIcon } from "lucide-react";


interface EditUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: User | null;
  onUpdated: () => void;
}

export const EditUserModal: React.FC<EditUserModalProps> = ({
  isOpen,
  onClose,
  user,
  onUpdated,
}) => {
  const [formData, setFormData] = useState<{
    name: string;
    email: string;
    password: string;
    status: string;
    role_id: number | undefined;
  }>({
    name: "",
    email: "",
    password: "",
    status: "active",
    role_id: undefined,
  });

  const [loading, setLoading] = useState(false);
  const { success, error } = useToast();

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || "",
        email: user.email || "",
        password: "",
        status: user.status || "active",
        role_id: user.role_id ?? undefined,
      });
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    if (!formData.name.trim() || !formData.email.trim()) {
      error("Name and email are required.");
      return;
    }

    setLoading(true);
    try {
      const payload: UserUpdate = {
        name: formData.name.trim(),
        email: formData.email.trim(),
        status: formData.status,
        role_id: formData.role_id,
      };


      if (formData.password.trim()) {
        payload.password = formData.password.trim();
      }

      await userService.updateUser(user.id, payload);
      success(`User "${formData.name}" updated successfully!`);
      onUpdated();
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update user";
      error(message);
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Edit Team Member"
      subtitle={`Modify profile, permissions, and alerts for ${user.name}`}
      maxWidth={540}
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
        <div className="form-group">
          <label className="form-label" htmlFor="user-edit-name">
            <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
              <UserIcon size={14} /> Full Name *
            </span>
          </label>
          <input
            id="user-edit-name"
            required
            className="form-control"
            placeholder="Jane Doe"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="user-edit-email">
            <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
              <Mail size={14} /> Email Address *
            </span>
          </label>
          <input
            id="user-edit-email"
            type="email"
            required
            className="form-control"
            placeholder="jane@company.com"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="user-edit-password">
            New Password (Optional)
          </label>
          <input
            id="user-edit-password"
            type="password"
            className="form-control"
            placeholder="Leave blank to keep existing password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          />
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px", display: "block" }}>
            Only enter a value if you wish to reset or change this member&apos;s password.
          </span>
        </div>

        <div className="form-grid-2">
          <div className="form-group">
            <label className="form-label" htmlFor="user-edit-role">
              <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
                <Shield size={14} /> Access Role
              </span>
            </label>
            <select
              id="user-edit-role"
              className="form-control"
              value={formData.role_id ?? ""}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  role_id: e.target.value ? Number(e.target.value) : undefined,
                })
              }
            >
              <option value="">Standard Member</option>
              <option value="1">Super Admin (Full Access)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="user-edit-status">Account Status</label>
            <select
              id="user-edit-status"
              className="form-control"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive / Suspended</option>
            </select>
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "12px", flexWrap: "wrap" }}>

          <button type="button" onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            <span>Save Changes</span>
          </button>
        </div>
      </form>
    </Modal>
  );
};
