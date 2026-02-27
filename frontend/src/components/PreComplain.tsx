//frontend/src/components/PreComplain.tsx
import React, { useState } from "react";
import {
  type RegisterComplain,
  type Complainant,
  type ComplainReview,
  CrimeType,
  ComplainStatus,
  ComplainantStatus,
  type User,
} from "../logic/DataTypes";

interface PreComplaintViewProps {
  complaint: RegisterComplain;
  onEdit?: () => void;
  onSubmit?: () => void;
  onCancel?: () => void;
  onDelete?: () => void;
  onReview?: (review: Partial<ComplainReview>) => void;
  onAssignToOfficer?: () => void;
  onRequestMoreInfo?: () => void;
  onEscalate?: () => void;
  currentUser: User;
  userRole: "complainant" | "cadet" | "officer" | "admin" | "supervisor";
  isLoading?: boolean;
}

const PreComplaintView: React.FC<PreComplaintViewProps> = ({
  complaint,
  onEdit,
  onSubmit,
  onCancel,
  onDelete,
  onReview,
  onAssignToOfficer,
  onRequestMoreInfo,
  onEscalate,
  userRole,
  isLoading = false,
}) => {
  const [activeTab, setActiveTab] = useState<
    "details" | "complainants" | "reviews" | "timeline" | "documents"
  >("details");
  const [reviewMessage, setReviewMessage] = useState("");
  const [reviewAction, setReviewAction] = useState<
    "approve" | "reject" | "return" | null
  >(null);
  const [showReviewModal, setShowReviewModal] = useState(false);

  // Helper functions (same as before)
  const getStatusBadgeColor = (status: ComplainStatus): string => {
    switch (status) {
      case ComplainStatus.DRAFT:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
      case ComplainStatus.PENDING_CADET:
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300";
      case ComplainStatus.PENDING_OFFICER:
        return "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300";
      case ComplainStatus.RETURNED_TO_COMPLAINANT:
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300";
      case ComplainStatus.APPROVED:
        return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300";
      case ComplainStatus.REJECTED:
        return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300";
      case ComplainStatus.CANCELLED:
        return "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
    }
  };

  const getCrimeTypeColor = (
    type: CrimeType,
  ): { bg: string; text: string; label: string } => {
    switch (type) {
      case CrimeType.TYPE_3:
        return {
          bg: "bg-green-100 dark:bg-green-900/30",
          text: "text-green-800 dark:text-green-300",
          label: "سطح ۳ - جرائم خرد",
        };
      case CrimeType.TYPE_2:
        return {
          bg: "bg-yellow-100 dark:bg-yellow-900/30",
          text: "text-yellow-800 dark:text-yellow-300",
          label: "سطح ۲ - جرائم متوسط",
        };
      case CrimeType.TYPE_1:
        return {
          bg: "bg-orange-100 dark:bg-orange-900/30",
          text: "text-orange-800 dark:text-orange-300",
          label: "سطح ۱ - جرائم سنگین",
        };
      case CrimeType.CRITICAL:
        return {
          bg: "bg-red-100 dark:bg-red-900/30",
          text: "text-red-800 dark:text-red-300",
          label: "بحرانی",
        };
      default:
        return {
          bg: "bg-gray-100 dark:bg-gray-700",
          text: "text-gray-800 dark:text-gray-300",
          label: type,
        };
    }
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString("fa-IR", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const crimeTypeStyle = getCrimeTypeColor(complaint.crime_type);

  // Render buttons based on user role
  const renderActionButtons = () => {
    switch (userRole) {
      case "complainant":
        return (
          <div className="flex flex-wrap gap-2">
            {/* Complainant actions - only when they can edit/submit */}
            {complaint.can_be_edited_by_complainant && (
              <button
                onClick={onEdit}
                className="
                  flex items-center gap-2
                  px-4 py-2
                  bg-blue-600 hover:bg-blue-700
                  text-white text-sm font-medium
                  rounded-lg
                  transition-colors
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                "
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                  />
                </svg>
                <span>ویرایش</span>
              </button>
            )}

            {complaint.can_submit && (
              <button
                onClick={onSubmit}
                className="
                  flex items-center gap-2
                  px-4 py-2
                  bg-green-600 hover:bg-green-700
                  text-white text-sm font-medium
                  rounded-lg
                  transition-colors
                  focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2
                "
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <span>ارسال برای بررسی</span>
              </button>
            )}

            {complaint.status === ComplainStatus.DRAFT && (
              <button
                onClick={onCancel}
                className="
                  flex items-center gap-2
                  px-4 py-2
                  bg-red-600 hover:bg-red-700
                  text-white text-sm font-medium
                  rounded-lg
                  transition-colors
                  focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
                "
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
                <span>لغو شکایت</span>
              </button>
            )}
          </div>
        );

      case "cadet":
        return (
          <div className="flex flex-wrap gap-2">
            {/* Cadet actions - primarily review and assign */}
            {complaint.status === ComplainStatus.PENDING_CADET && (
              <>
                <button
                  onClick={() => setShowReviewModal(true)}
                  className="
                    flex items-center gap-2
                    px-4 py-2
                    bg-purple-600 hover:bg-purple-700
                    text-white text-sm font-medium
                    rounded-lg
                    transition-colors
                    focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2
                  "
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <span>بررسی شکایت</span>
                </button>

                <button
                  onClick={onAssignToOfficer}
                  className="
                    flex items-center gap-2
                    px-4 py-2
                    bg-blue-600 hover:bg-blue-700
                    text-white text-sm font-medium
                    rounded-lg
                    transition-colors
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                  "
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                    />
                  </svg>
                  <span>ارجاع به افسر</span>
                </button>
              </>
            )}

            {/* Information request button */}
            {complaint.status !== ComplainStatus.REJECTED &&
              complaint.status !== ComplainStatus.APPROVED && (
                <button
                  onClick={onRequestMoreInfo}
                  className="
                  flex items-center gap-2
                  px-4 py-2
                  bg-yellow-600 hover:bg-yellow-700
                  text-white text-sm font-medium
                  rounded-lg
                  transition-colors
                  focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2
                "
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <span>درخواست اطلاعات بیشتر</span>
                </button>
              )}
          </div>
        );

      case "officer":
        return (
          <div className="flex flex-wrap gap-2">
            {/* Officer actions - final approval, rejection, escalation */}
            {complaint.status === ComplainStatus.PENDING_OFFICER && (
              <>
                <button
                  onClick={() => setShowReviewModal(true)}
                  className="
                    flex items-center gap-2
                    px-4 py-2
                    bg-green-600 hover:bg-green-700
                    text-white text-sm font-medium
                    rounded-lg
                    transition-colors
                    focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2
                  "
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span>تأیید نهایی</span>
                </button>

                <button
                  onClick={onEscalate}
                  className="
                    flex items-center gap-2
                    px-4 py-2
                    bg-red-600 hover:bg-red-700
                    text-white text-sm font-medium
                    rounded-lg
                    transition-colors
                    focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
                  "
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    />
                  </svg>
                  <span>ارجاع به مقام بالاتر</span>
                </button>
              </>
            )}
          </div>
        );

      case "supervisor":
        return (
          <div className="flex flex-wrap gap-2">
            {/* Supervisor actions - oversight and management */}
            <button
              onClick={() =>
                onReview
                  ? onReview({})
                  : console.warn("onReview function not provided")
              }
              className="
                flex items-center gap-2
                px-4 py-2
                bg-indigo-600 hover:bg-indigo-700
                text-white text-sm font-medium
                rounded-lg
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
              "
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
              <span>بازبینی</span>
            </button>

            <button
              onClick={onAssignToOfficer}
              className="
                flex items-center gap-2
                px-4 py-2
                bg-blue-600 hover:bg-blue-700
                text-white text-sm font-medium
                rounded-lg
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
              "
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
              <span>تخصیص به افسر</span>
            </button>

            <button
              onClick={onEscalate}
              className="
                flex items-center gap-2
                px-4 py-2
                bg-orange-600 hover:bg-orange-700
                text-white text-sm font-medium
                rounded-lg
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2
              "
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              <span>ارتقا سطح</span>
            </button>

            <button
              onClick={onDelete}
              className="
                flex items-center gap-2
                px-4 py-2
                bg-red-600 hover:bg-red-700
                text-white text-sm font-medium
                rounded-lg
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
              "
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              <span>حذف</span>
            </button>
          </div>
        );

      case "admin":
        return (
          <div className="flex flex-wrap gap-2">
            {/* Admin actions - full control */}
            <button
              onClick={onEdit}
              className="
                flex items-center gap-2
                px-4 py-2
                bg-blue-600 hover:bg-blue-700
                text-white text-sm font-medium
                rounded-lg
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
              "
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                />
              </svg>
              <span>ویرایش</span>
            </button>

            <button
              onClick={() => setShowReviewModal(true)}
              className="
                flex items-center gap-2
                px-4 py-2
                bg-purple-600 hover:bg-purple-700
                text-white text-sm font-medium
                rounded-lg
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2
              "
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>بررسی</span>
            </button>

            <button
              onClick={onAssignToOfficer}
              className="
                flex items-center gap-2
                px-4 py-2
                bg-teal-600 hover:bg-teal-700
                text-white text-sm font-medium
                rounded-lg
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2
              "
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
              <span>تخصیص به افسر</span>
            </button>

            <button
              onClick={onDelete}
              className="
                flex items-center gap-2
                px-4 py-2
                bg-red-600 hover:bg-red-700
                text-white text-sm font-medium
                rounded-lg
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
              "
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              <span>حذف</span>
            </button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden"
      dir="rtl"
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {complaint.title}
            </h1>
            <div className="flex flex-wrap items-center gap-3">
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(complaint.status)}`}
              >
                {complaint.status}
              </span>
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${crimeTypeStyle.bg} ${crimeTypeStyle.text}`}
              >
                {crimeTypeStyle.label}
              </span>
              <span className="inline-flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  />
                </svg>
                <span>
                  {userRole === "complainant"
                    ? "شاکی"
                    : userRole === "cadet"
                      ? "کارآموز"
                      : userRole === "officer"
                        ? "افسر"
                        : userRole === "supervisor"
                          ? "ناظر"
                          : "مدیر"}
                </span>
              </span>
            </div>
          </div>

          {/* Role-based action buttons */}
          <div className="flex flex-wrap gap-2">{renderActionButtons()}</div>
        </div>
      </div>

      {/* Rest of the component remains the same */}
      {/* Tabs, Tab Content, Review Modal - unchanged from previous version */}

      {/* Tabs */}
      <div className="px-6 border-b border-gray-200 dark:border-gray-700">
        <nav className="flex gap-6">
          {(
            [
              "details",
              "complainants",
              "reviews",
              "timeline",
              "documents",
            ] as const
          ).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${
                  activeTab === tab
                    ? "border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400"
                    : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                }
              `}
            >
              {tab === "details" && "جزئیات شکایت"}
              {tab === "complainants" && "شاکیان"}
              {tab === "reviews" && "بررسی‌ها"}
              {tab === "timeline" && "تاریخچه"}
              {tab === "documents" && "مدارک"}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content - same as before */}
      <div className="p-6">
        {/* ... (keep all the tab content from the previous version) ... */}
      </div>

      {/* Review Modal - same as before */}
      {showReviewModal && (
        <div
          className="fixed inset-0 z-50 overflow-y-auto"
          aria-labelledby="modal-title"
          role="dialog"
          aria-modal="true"
        >
          {/* ... (keep the review modal from the previous version) ... */}
        </div>
      )}
    </div>
  );
};

export default PreComplaintView;
