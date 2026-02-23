//frontend/src/components/AddComplain.tsx
import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  CrimeType,
  ComplainStatus,
  ComplainantStatus,
  type RegisterComplain,
  type RegisterComplainFormData,
  type User,
  type Complainant
} from "../logic/DataTypes.ts"

interface AddComplainProps {
  onClose: () => void;
  onSave: (complain: RegisterComplain) => void;
  initialData?: RegisterComplain;
  currentUser: User;
  availableUsers?: User[]; // For adding additional complainants
}

const AddComplain: React.FC<AddComplainProps> = ({
  onClose,
  onSave,
  initialData,
  currentUser,
  availableUsers = [],
}) => {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const formRef = useRef<HTMLFormElement>(null);
  
  const [additionalComplainants, setAdditionalComplainants] = useState<
    { userId: string; relationship: string }[]
  >([]);
  
  const [selectedCrimeType, setSelectedCrimeType] = useState<CrimeType>(
    initialData?.crime_type || CrimeType.TYPE_1
  );

  // Initialize form with initial data
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    dialog.showModal();

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  // Handle click outside to close
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (event.target === dialog) {
        onClose();
      }
    };

    dialog.addEventListener("click", handleClickOutside);
    return () => dialog.removeEventListener("click", handleClickOutside);
  }, [onClose]);

  // Add additional complainant
  const addComplainant = useCallback(() => {
    setAdditionalComplainants(prev => [
      ...prev,
      { userId: "", relationship: "" }
    ]);
  }, []);

  // Remove additional complainant
  const removeComplainant = useCallback((index: number) => {
    setAdditionalComplainants(prev => prev.filter((_, i) => i !== index));
  }, []);

  // Update complainant field
  const updateComplainant = useCallback((
    index: number,
    field: keyof typeof additionalComplainants[0],
    value: string
  ) => {
    setAdditionalComplainants(prev =>
      prev.map((item, i) =>
        i === index ? { ...item, [field]: value } : item
      )
    );
  }, []);

  // Format datetime for input field
  const formatDateTimeForInput = (date?: Date): string => {
    if (!date) return "";
    const d = new Date(date);
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 16);
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    const formData = new FormData(e.currentTarget);
    const title = (formData.get("title") as string).trim();
    const description = (formData.get("description") as string).trim();
    const incident_datetime = formData.get("incident_datetime") as string;
    const incident_location = (formData.get("incident_location") as string).trim();
    const crime_type = formData.get("crime_type") as CrimeType;

    // Validation
    if (!title) {
      alert("عنوان شکایت الزامی است!");
      return;
    }

    if (!description) {
      alert("شرح شکایت الزامی است!");
      return;
    }

    if (!incident_datetime) {
      alert("زمان وقوع حادثه الزامی است!");
      return;
    }

    if (!incident_location) {
      alert("محل وقوع حادثه الزامی است!");
      return;
    }

    // Create complainants array
    const complainants: Partial<Complainant>[] = additionalComplainants
      .filter(c => c.userId && c.userId.trim() !== "")
      .map(c => ({
        user: c.userId,
        relationship_to_incident: c.relationship,
        status: ComplainantStatus.PENDING
      }));

    const complain: RegisterComplain = {
      id: initialData?.id || crypto.randomUUID(),
      creator: currentUser,
      title,
      description,
      incident_datetime: new Date(incident_datetime).toISOString(),
      incident_location,
      crime_type,
      created_at: initialData?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString(),
      status: initialData?.status || ComplainStatus.DRAFT,
      revision_count: initialData?.revision_count || 0,
      max_revisions: 3,
      complainants: complainants as Complainant[],
      can_be_edited_by_complainant: true,
      can_submit: true
    };

    onSave(complain);
    onClose();
  };

  // Get crime type label in Persian
  const getCrimeTypeLabel = (type: CrimeType): string => {
    switch (type) {
      case CrimeType.TYPE_3:
        return "سطح ۳ - جرائم خرد";
      case CrimeType.TYPE_2:
        return "سطح ۲ - جرائم متوسط";
      case CrimeType.TYPE_1:
        return "سطح ۱ - جرائم سنگین";
      case CrimeType.CRITICAL:
        return "بحرانی";
      default:
        return type;
    }
  };

  // Get crime type color
  const getCrimeTypeColor = (type: CrimeType): string => {
    switch (type) {
      case CrimeType.TYPE_3:
        return "green";
      case CrimeType.TYPE_2:
        return "yellow";
      case CrimeType.TYPE_1:
        return "orange";
      case CrimeType.CRITICAL:
        return "red";
      default:
        return "gray";
    }
  };

  return (
    <dialog
      ref={dialogRef}
      className="
        m-auto
        backdrop:bg-black/50
        backdrop:backdrop-blur-sm
        bg-transparent
        border-0
        p-0
        max-w-3xl w-full
        max-h-[95vh]
        overflow-hidden
        animate-in fade-in duration-200
        rtl
      "
      aria-labelledby="complain-dialog-title"
      aria-modal="true"
      role="dialog"
      dir="rtl"
    >
      <form
        ref={formRef}
        onSubmit={handleSubmit}
        className="
          flex flex-col
          bg-white dark:bg-gray-800
          rounded-xl shadow-2xl
          max-h-[95vh]
          overflow-hidden
        "
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2
              id="complain-dialog-title"
              className="text-xl font-semibold text-gray-900 dark:text-white"
            >
              {initialData ? "ویرایش شکایت" : "ثبت شکایت جدید"}
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="
                p-2 rounded-lg
                text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200
                hover:bg-gray-100 dark:hover:bg-gray-700
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-blue-500
              "
              aria-label="بستن"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {initialData 
              ? "اطلاعات شکایت خود را به‌روزرسانی کنید" 
              : "لطفاً اطلاعات شکایت خود را با دقت وارد کنید"}
          </p>
        </div>

        {/* Form Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Title */}
          <div className="space-y-2">
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              عنوان شکایت *
            </label>
            <input
              id="title"
              name="title"
              type="text"
              required
              maxLength={255}
              defaultValue={initialData?.title}
              className="
                w-full px-4 py-3
                border border-gray-300 dark:border-gray-600
                rounded-lg
                bg-white dark:bg-gray-700
                text-gray-900 dark:text-white
                placeholder-gray-500 dark:placeholder-gray-400
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                transition-shadow
                text-right
              "
              placeholder="مثال: سرقت از منزل"
              autoComplete="off"
              autoFocus
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              شرح کامل شکایت *
            </label>
            <textarea
              id="description"
              name="description"
              rows={5}
              required
              defaultValue={initialData?.description}
              className="
                w-full px-4 py-3
                border border-gray-300 dark:border-gray-600
                rounded-lg
                bg-white dark:bg-gray-700
                text-gray-900 dark:text-white
                placeholder-gray-500 dark:placeholder-gray-400
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                transition-shadow
                resize-none
                text-right
              "
              placeholder="شرح کامل ماجرا، جزئیات حادثه، خسارات وارده و ..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Incident Date & Time */}
            <div className="space-y-2">
              <label htmlFor="incident_datetime" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                زمان تقریبی وقوع *
              </label>
              <input
                id="incident_datetime"
                name="incident_datetime"
                type="datetime-local"
                required
                defaultValue={formatDateTimeForInput(
                  initialData?.incident_datetime ? new Date(initialData.incident_datetime) : undefined
                )}
                className="
                  w-full px-4 py-3
                  border border-gray-300 dark:border-gray-600
                  rounded-lg
                  bg-white dark:bg-gray-700
                  text-gray-900 dark:text-white
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                "
              />
            </div>

            {/* Crime Type */}
            <div className="space-y-2">
              <label htmlFor="crime_type" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                نوع جرم *
              </label>
              <select
                id="crime_type"
                name="crime_type"
                required
                value={selectedCrimeType}
                onChange={(e) => setSelectedCrimeType(e.target.value as CrimeType)}
                className="
                  w-full px-4 py-3
                  border border-gray-300 dark:border-gray-600
                  rounded-lg
                  bg-white dark:bg-gray-700
                  text-gray-900 dark:text-white
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                  appearance-none
                  cursor-pointer
                "
              >
                {Object.values(CrimeType).map((type) => (
                  <option key={type} value={type}>
                    {getCrimeTypeLabel(type)}
                  </option>
                ))}
              </select>
              
              {/* Crime type indicator */}
              <div className="flex items-center gap-2 mt-2">
                <div 
                  className={`w-3 h-3 rounded-full bg-${getCrimeTypeColor(selectedCrimeType)}-500`}
                />
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  سطح اهمیت: {getCrimeTypeLabel(selectedCrimeType)}
                </span>
              </div>
            </div>
          </div>

          {/* Incident Location */}
          <div className="space-y-2">
            <label htmlFor="incident_location" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              محل وقوع *
            </label>
            <input
              id="incident_location"
              name="incident_location"
              type="text"
              required
              maxLength={300}
              defaultValue={initialData?.incident_location}
              className="
                w-full px-4 py-3
                border border-gray-300 dark:border-gray-600
                rounded-lg
                bg-white dark:bg-gray-700
                text-gray-900 dark:text-white
                placeholder-gray-500 dark:placeholder-gray-400
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                transition-shadow
                text-right
              "
              placeholder="آدرس کامل محل وقوع حادثه"
            />
          </div>

          {/* Additional Complainants Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                شاکیان اضافی
              </label>
              <button
                type="button"
                onClick={addComplainant}
                className="
                  flex items-center gap-2
                  px-3 py-1.5
                  text-sm font-medium
                  text-blue-600 dark:text-blue-400
                  bg-blue-50 dark:bg-blue-900/20
                  hover:bg-blue-100 dark:hover:bg-blue-900/30
                  rounded-lg
                  transition-colors
                  focus:outline-none focus:ring-2 focus:ring-blue-500
                "
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>افزودن شاکی</span>
              </button>
            </div>

            {/* Current user as primary complainant */}
            <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium">
                  {currentUser.first_name?.[0] || currentUser.username?.[0] || "ش"}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {currentUser.first_name && currentUser.last_name 
                      ? `${currentUser.first_name} ${currentUser.last_name}`
                      : currentUser.username || "شاکی اصلی"}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    شاکی اصلی • {currentUser.email}
                  </p>
                </div>
                <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-2 py-1 rounded">
                  اصلی
                </span>
              </div>
            </div>

            {/* Additional complainants list */}
            {additionalComplainants.map((complainant, index) => (
              <div key={index} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    شاکی {index + 1}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeComplainant(index)}
                    className="
                      p-1 rounded-lg
                      text-red-500 hover:text-red-700
                      hover:bg-red-50 dark:hover:bg-red-900/20
                      transition-colors
                    "
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <select
                    value={complainant.userId}
                    onChange={(e) => updateComplainant(index, "userId", e.target.value)}
                    className="
                      w-full px-4 py-2
                      border border-gray-300 dark:border-gray-600
                      rounded-lg
                      bg-white dark:bg-gray-700
                      text-gray-900 dark:text-white
                      focus:outline-none focus:ring-2 focus:ring-blue-500
                    "
                  >
                    <option value="">انتخاب کاربر</option>
                    {availableUsers
                      .filter(u => u.id !== currentUser.id)
                      .map(user => (
                        <option key={user.id} value={user.id}>
                          {user.first_name && user.last_name 
                            ? `${user.first_name} ${user.last_name}`
                            : user.username || user.email}
                        </option>
                      ))
                    }
                  </select>
                  
                  <input
                    type="text"
                    value={complainant.relationship}
                    onChange={(e) => updateComplainant(index, "relationship", e.target.value)}
                    placeholder="رابطه با حادثه (اختیاری)"
                    className="
                      w-full px-4 py-2
                      border border-gray-300 dark:border-gray-600
                      rounded-lg
                      bg-white dark:bg-gray-700
                      text-gray-900 dark:text-white
                      placeholder-gray-500 dark:placeholder-gray-400
                      focus:outline-none focus:ring-2 focus:ring-blue-500
                      text-right
                    "
                  />
                </div>
              </div>
            ))}

            {additionalComplainants.length === 0 && (
              <div className="text-center py-6 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
                <p className="text-gray-500 dark:text-gray-400">
                  شاکی دیگری اضافه نشده است. برای افزودن شاکی کلیک کنید.
                </p>
              </div>
            )}
          </div>

          {/* Status information for existing complaint */}
          {initialData && (
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <div className="text-blue-600 dark:text-blue-400">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    وضعیت فعلی: {initialData.status}
                  </p>
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    تعداد بازبینی‌ها: {initialData.revision_count} از {initialData.max_revisions}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              * فیلدهای الزامی
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={onClose}
                className="
                  px-5 py-2.5
                  text-sm font-medium
                  text-gray-700 dark:text-gray-300
                  bg-gray-100 dark:bg-gray-700
                  hover:bg-gray-200 dark:hover:bg-gray-600
                  rounded-lg
                  transition-colors
                  focus:outline-none focus:ring-2 focus:ring-gray-500
                "
              >
                انصراف
              </button>
              <button
                type="submit"
                className="
                  px-5 py-2.5
                  text-sm font-medium text-white
                  bg-gradient-to-r from-blue-600 to-blue-700
                  hover:from-blue-700 hover:to-blue-800
                  rounded-lg
                  transition-all
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                  shadow-sm
                  disabled:opacity-50 disabled:cursor-not-allowed
                "
              >
                {initialData ? "به‌روزرسانی شکایت" : "ثبت شکایت"}
              </button>
            </div>
          </div>
        </div>
      </form>
    </dialog>
  );
};

export default AddComplain;