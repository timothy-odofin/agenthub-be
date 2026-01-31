import { Lock, User, Mail, UserCircle, CheckCircle2 } from "lucide-react";

interface SignupProgressProps {
  progress: number;
  fieldsRemaining: number;
  currentStep: string;
}

interface Step {
  id: string;
  icon: React.ReactNode;
  label: string;
}

export const SignupProgress: React.FC<SignupProgressProps> = ({
  progress,
  fieldsRemaining,
  currentStep,
}) => {
  const steps: Step[] = [
    { id: "email", icon: <Mail className="w-4 h-4" />, label: "Email" },
    { id: "username", icon: <UserCircle className="w-4 h-4" />, label: "Username" },
    { id: "password", icon: <Lock className="w-4 h-4" />, label: "Password" },
    { id: "firstname", icon: <User className="w-4 h-4" />, label: "First Name" },
    { id: "lastname", icon: <User className="w-4 h-4" />, label: "Last Name" },
  ];

  const currentStepIndex = steps.findIndex((step) => step.id === currentStep);

  return (
    <div className="w-full">
      {/* Step Indicators */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-gray-600 text-xs font-semibold">Progress</span>
          <span className="text-blue-600 text-xs font-bold">{progress}%</span>
        </div>
        
        <div className="flex items-center gap-2">
          {steps.map((step, index) => {
            const isActive = step.id === currentStep;
            const isCompleted = index < currentStepIndex;
            
            return (
              <div
                key={step.id}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full transition-all ${
                  isActive
                    ? "bg-blue-100 border border-blue-300"
                    : isCompleted
                    ? "bg-green-100 border border-green-300"
                    : "bg-gray-100 border border-gray-200"
                }`}
              >
                <span
                  className={`${
                    isActive
                      ? "text-blue-600"
                      : isCompleted
                      ? "text-green-600"
                      : "text-gray-400"
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  ) : (
                    step.icon
                  )}
                </span>
                <span
                  className={`text-[10px] font-semibold uppercase tracking-wider ${
                    isActive
                      ? "text-blue-700"
                      : isCompleted
                      ? "text-green-700"
                      : "text-gray-400"
                  }`}
                >
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>

        <span className="text-gray-500 text-xs font-medium">
          {fieldsRemaining} {fieldsRemaining === 1 ? "field" : "fields"} left
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden shadow-inner">
        <div
          className="bg-gradient-to-r from-blue-600 to-purple-600 h-full rounded-full transition-all duration-500 ease-out shadow-lg"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};
