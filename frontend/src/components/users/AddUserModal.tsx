"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { userService } from "@/services/userService";
import { useToast } from "@/context/ToastContext";
import { UserCreate } from "@/types";
import { UserPlus, Loader2 } from "lucide-react";

interface AddUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export const AddUserModal: React.FC<AddUserModalProps> = ({
  isOpen,
  onClose,
  onCreated,
}) => {
  const [formData, setFormData] = useState<UserCreate>({
    name: "",
    email: "",
    password: "",
    status: "active",
  });
  const [loading, setLoading] = useState(false);
  const { success, error } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.password) {
      error("Name, email, and password are required.");
      return;
    }

    setLoading(true);
    try {
      await userService.createUser(formData);
      success("User account registered successfully!");
      onCreated();
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to create user";
      error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add Team Member"
      subtitle="Create a new user account with platform access"
      maxWidth={520}
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div className="form-group">
          <label className="form-label" htmlFor="user-create-name">Full Name *</label>
          <input
            id="user-create-name"
            required
            className="form-control"
            placeholder="Jane Doe"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="user-create-email">Email Address *</label>
          <input
            id="user-create-email"
            type="email"
            required
            className="form-control"
            placeholder="jane@company.com"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="user-create-password">Initial Password *</label>
          <input
            id="user-create-password"
            type="password"
            required
            className="form-control"
            placeholder="••••••••••••"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          />
        </div>

        <div className="form-grid-2">
          <div className="form-group">
            <label className="form-label" htmlFor="user-create-role">Access Role</label>
            <select
              id="user-create-role"
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
              <option value="1">Super Admin</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="user-create-status">Account Status</label>
            <select
              id="user-create-status"
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
            {loading ? <Loader2 size={16} className="animate-spin" /> : <UserPlus size={16} />}
            <span>Create User</span>
          </button>
        </div>
      </form>
    </Modal>
  );
};
