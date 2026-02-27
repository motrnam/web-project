//frontend/src/components/ComplainList.tsx
import React, { useState } from "react";
import AddComplain from "./AddComplain";
import {
  type RegisterComplain,
  type User,
  CrimeType,
  ComplainStatus,
} from "../logic/DataTypes";

// Example parent component that lists complaints
const ComplaintList: React.FC = () => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [complaints, setComplaints] = useState<RegisterComplain[]>([]);
  const [editingComplaint, setEditingComplaint] = useState<
    RegisterComplain | undefined
  >();

  // Mock current user (in real app, get from auth context)
  const currentUser: User = {
    id: "user-123",
    username: "johndoe",
    email: "john@example.com",
    first_name: "John",
    last_name: "Doe",
    full_name: "John Doe",
  };

  // Mock available users for additional complainants
  const availableUsers: User[] = [
    currentUser,
    {
      id: "user-456",
      username: "janesmith",
      email: "jane@example.com",
      first_name: "Jane",
      last_name: "Smith",
      full_name: "Jane Smith",
    },
    {
      id: "user-789",
      username: "bobjohnson",
      email: "bob@example.com",
      first_name: "Bob",
      last_name: "Johnson",
      full_name: "Bob Johnson",
    },
  ];

  // Handle save new complaint
  const handleSaveComplaint = (newComplaint: RegisterComplain) => {
    if (editingComplaint) {
      // Update existing complaint
      setComplaints((prev) =>
        prev.map((c) => (c.id === newComplaint.id ? newComplaint : c)),
      );
      console.log("Complaint updated:", newComplaint);
    } else {
      // Add new complaint
      setComplaints((prev) => [newComplaint, ...prev]);
      console.log("New complaint saved:", newComplaint);
    }

    // Close modal and reset editing state
    setIsAddModalOpen(false);
    setEditingComplaint(undefined);
  };

  // Handle edit complaint
  const handleEditComplaint = (complaint: RegisterComplain) => {
    setEditingComplaint(complaint);
    setIsAddModalOpen(true);
  };

  // Handle close modal
  const handleCloseModal = () => {
    setIsAddModalOpen(false);
    setEditingComplaint(undefined);
  };

  // Mock data for demonstration
  const mockComplaint: RegisterComplain = {
    id: "complaint-001",
    creator: currentUser,
    title: "سرقت از منزل مسکونی",
    description:
      "در تاریخ ۱۵ دی‌ماه ۱۴۰۲، افراد ناشناس با شکستن درب ورودی وارد منزل شده و اقدام به سرقت طلا و وجه نقد نموده‌اند.",
    incident_datetime: "2024-01-05T14:30:00Z",
    incident_location: "تهران، خیابان ولیعصر، کوچه نور، پلاک ۱۲",
    crime_type: CrimeType.TYPE_1,
    created_at: "2024-01-06T10:00:00Z",
    updated_at: "2024-01-06T10:00:00Z",
    status: ComplainStatus.DRAFT,
    revision_count: 0,
    max_revisions: 3,
    complainants: [
      {
        user: currentUser,
        relationship_to_incident: "مالک منزل",
        status: "APPROVED",
        created_at: "2024-01-06T10:00:00Z",
      },
    ],
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header with action buttons */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            مدیریت شکایات
          </h1>

          <div className="flex gap-3">
            {/* Button to add new complaint */}
            <button
              onClick={() => {
                setEditingComplaint(undefined);
                setIsAddModalOpen(true);
              }}
              className="
                flex items-center gap-2
                px-4 py-2
                bg-blue-600 hover:bg-blue-700
                text-white font-medium
                rounded-lg
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
              "
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              <span>ثبت شکایت جدید</span>
            </button>

            {/* Button to edit example complaint (for demo) */}
            <button
              onClick={() => handleEditComplaint(mockComplaint)}
              className="
                flex items-center gap-2
                px-4 py-2
                bg-gray-600 hover:bg-gray-700
                text-white font-medium
                rounded-lg
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2
              "
            >
              <svg
                className="w-5 h-5"
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
              <span>ویرایش نمونه</span>
            </button>
          </div>
        </div>

        {/* Complaints list */}
        <div className="grid gap-4">
          {complaints.length > 0 ? (
            complaints.map((complaint) => (
              <div
                key={complaint.id}
                className="
                  bg-white dark:bg-gray-800
                  rounded-lg shadow-md
                  p-6
                  border border-gray-200 dark:border-gray-700
                "
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      {complaint.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                      {complaint.description}
                    </p>

                    <div className="flex flex-wrap gap-4 text-sm">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500 dark:text-gray-500">
                          زمان وقوع:
                        </span>
                        <span className="text-gray-900 dark:text-white">
                          {new Date(
                            complaint.incident_datetime,
                          ).toLocaleDateString("fa-IR")}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-gray-500 dark:text-gray-500">
                          محل:
                        </span>
                        <span className="text-gray-900 dark:text-white">
                          {complaint.incident_location}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-gray-500 dark:text-gray-500">
                          نوع جرم:
                        </span>
                        <span className="text-gray-900 dark:text-white">
                          {complaint.crime_type}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEditComplaint(complaint)}
                      className="
                        p-2 text-blue-600 hover:text-blue-800
                        hover:bg-blue-50 dark:hover:bg-blue-900/20
                        rounded-lg transition-colors
                      "
                    >
                      <svg
                        className="w-5 h-5"
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
                    </button>
                  </div>
                </div>

                {/* Status badge */}
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <span
                    className={`
                    inline-flex items-center px-3 py-1 rounded-full text-xs font-medium
                    ${complaint.status === ComplainStatus.DRAFT ? "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300" : ""}
                    ${complaint.status === ComplainStatus.PENDING_CADET ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300" : ""}
                    ${complaint.status === ComplainStatus.APPROVED ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300" : ""}
                    ${complaint.status === ComplainStatus.REJECTED ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300" : ""}
                  `}
                  >
                    {complaint.status}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                هیچ شکایتی ثبت نشده
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                برای ثبت اولین شکایت خود، دکمه "ثبت شکایت جدید" را کلیک کنید.
              </p>
            </div>
          )}
        </div>

        {/* Add/Edit Complaint Modal */}
        {isAddModalOpen && (
          <AddComplain
            onClose={handleCloseModal}
            onSave={handleSaveComplaint}
            initialData={editingComplaint}
            currentUser={currentUser}
            availableUsers={availableUsers}
          />
        )}
      </div>
    </div>
  );
};

export default ComplaintList;

// Example with React Router integration
import { useNavigate, useParams } from "react-router-dom";

const ComplaintDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [isEditMode, setIsEditMode] = useState(false);
  const [complaint, setComplaint] = useState<RegisterComplain | null>(null);

  // Fetch complaint data
  React.useEffect(() => {
    if (id) {
      // In real app, fetch from API
      // fetchComplaint(id).then(setComplaint);
    }
  }, [id]);

  const handleUpdateComplaint = (updatedComplaint: RegisterComplain) => {
    // In real app, send to API
    // api.updateComplaint(updatedComplaint).then(() => {
    setComplaint(updatedComplaint);
    setIsEditMode(false);
    // });
  };

  if (!complaint) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      {/* Complaint detail view */}
      <div className="mb-4">
        <button
          onClick={() => setIsEditMode(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          ویرایش شکایت
        </button>
      </div>

      {/* Complaint details */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">{complaint.title}</h2>
        <p className="text-gray-700 mb-4">{complaint.description}</p>
        {/* Other details */}
      </div>

      {/* Edit modal */}
      {isEditMode && (
        <AddComplain
          onClose={() => setIsEditMode(false)}
          onSave={handleUpdateComplaint}
          initialData={complaint}
          currentUser={complaint.creator as User}
          availableUsers={[]} // Fetch available users
        />
      )}
    </div>
  );
};

// Example with form data submission to API
const ComplaintCreationFlow: React.FC = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmitToApi = async (complaint: RegisterComplain) => {
    setIsSubmitting(true);

    try {
      // Prepare data for API (remove helper properties)
      const apiData = {
        title: complaint.title,
        description: complaint.description,
        incident_datetime: complaint.incident_datetime,
        incident_location: complaint.incident_location,
        crime_type: complaint.crime_type,
        complainants: complaint.complainants?.map((c) => ({
          user_id: typeof c.user === "string" ? c.user : c.user.id,
          relationship_to_incident: c.relationship_to_incident,
        })),
      };

      // Send to API
      const response = await fetch("/api/complaints/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(apiData),
      });

      if (!response.ok) {
        throw new Error("Failed to create complaint");
      }

      const result = await response.json();
      console.log("Complaint created successfully:", result);

      // Show success message
      alert("شکایت با موفقیت ثبت شد");
    } catch (error) {
      console.error("Error creating complaint:", error);
      alert("خطا در ثبت شکایت. لطفاً مجدداً تلاش کنید.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AddComplain
      onClose={() => {}}
      onSave={handleSubmitToApi}
      currentUser={currentUser}
      availableUsers={[]}
    />
  );
};
