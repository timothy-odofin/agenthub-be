import { useState } from "react";
import { X, Link2, Copy, Check, Globe, Lock, Users, Calendar } from "lucide-react";

interface EnhancedShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  sessionTitle: string;
}

type ShareMode = "private" | "anyone-with-link" | "public";

export default function EnhancedShareModal({
  isOpen,
  onClose,
  sessionId,
  sessionTitle,
}: EnhancedShareModalProps) {
  const [shareMode, setShareMode] = useState<ShareMode>("anyone-with-link");
  const [copied, setCopied] = useState(false);
  const [allowComments, setAllowComments] = useState(true);
  const [expiryEnabled, setExpiryEnabled] = useState(false);
  const [expiryDays, setExpiryDays] = useState(7);

  // Generate shareable URL
  const shareUrl = `${window.location.origin}/main-dashboard/${sessionId}`;

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const handleCreateLink = () => {
    // Future: API call to create shareable link with settings
    console.log("Creating share link with settings:", {
      shareMode,
      allowComments,
      expiryEnabled,
      expiryDays,
    });
    alert("Share link created! (Backend API pending)");
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl mx-4 animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Share Chat</h2>
            <p className="text-sm text-gray-500 mt-1 truncate max-w-md">
              {sessionTitle}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Body - Scrollable */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Share Mode Selection */}
          <div>
            <label className="text-sm font-semibold text-gray-700 mb-3 block">
              Who can access this chat?
            </label>
            <div className="space-y-2">
              {/* Private */}
              <button
                onClick={() => setShareMode("private")}
                className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
                  shareMode === "private"
                    ? "border-blue-600 bg-blue-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <div className="flex items-start gap-3">
                  <Lock
                    className={`w-5 h-5 mt-0.5 ${
                      shareMode === "private" ? "text-blue-600" : "text-gray-600"
                    }`}
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p
                        className={`font-medium ${
                          shareMode === "private" ? "text-blue-900" : "text-gray-900"
                        }`}
                      >
                        Private
                      </p>
                      {shareMode === "private" && (
                        <div className="w-2 h-2 rounded-full bg-blue-600"></div>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      Only you can access this conversation
                    </p>
                  </div>
                </div>
              </button>

              {/* Anyone with link */}
              <button
                onClick={() => setShareMode("anyone-with-link")}
                className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
                  shareMode === "anyone-with-link"
                    ? "border-blue-600 bg-blue-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <div className="flex items-start gap-3">
                  <Link2
                    className={`w-5 h-5 mt-0.5 ${
                      shareMode === "anyone-with-link" ? "text-blue-600" : "text-gray-600"
                    }`}
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p
                        className={`font-medium ${
                          shareMode === "anyone-with-link"
                            ? "text-blue-900"
                            : "text-gray-900"
                        }`}
                      >
                        Anyone with the link
                      </p>
                      {shareMode === "anyone-with-link" && (
                        <div className="w-2 h-2 rounded-full bg-blue-600"></div>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      Anyone who has the link can view this conversation
                    </p>
                  </div>
                </div>
              </button>

              {/* Public */}
              <button
                onClick={() => setShareMode("public")}
                className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
                  shareMode === "public"
                    ? "border-blue-600 bg-blue-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <div className="flex items-start gap-3">
                  <Globe
                    className={`w-5 h-5 mt-0.5 ${
                      shareMode === "public" ? "text-blue-600" : "text-gray-600"
                    }`}
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p
                        className={`font-medium ${
                          shareMode === "public" ? "text-blue-900" : "text-gray-900"
                        }`}
                      >
                        Public on the web
                      </p>
                      {shareMode === "public" && (
                        <div className="w-2 h-2 rounded-full bg-blue-600"></div>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      Anyone on the internet can discover and view
                    </p>
                  </div>
                </div>
              </button>
            </div>
          </div>

          {/* Additional Options */}
          {shareMode !== "private" && (
            <div className="space-y-4 pt-4 border-t border-gray-200">
              <p className="text-sm font-semibold text-gray-700">
                Additional settings
              </p>

              {/* Allow Comments */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Users className="w-4 h-4 text-gray-600" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Allow comments
                    </p>
                    <p className="text-xs text-gray-500">
                      Let viewers leave comments on messages
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setAllowComments(!allowComments)}
                  className={`relative w-11 h-6 rounded-full transition-colors ${
                    allowComments ? "bg-blue-600" : "bg-gray-300"
                  }`}
                >
                  <div
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                      allowComments ? "translate-x-5" : ""
                    }`}
                  ></div>
                </button>
              </div>

              {/* Link Expiry */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Calendar className="w-4 h-4 text-gray-600" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Link expiration
                    </p>
                    <p className="text-xs text-gray-500">
                      Automatically disable link after time limit
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setExpiryEnabled(!expiryEnabled)}
                  className={`relative w-11 h-6 rounded-full transition-colors ${
                    expiryEnabled ? "bg-blue-600" : "bg-gray-300"
                  }`}
                >
                  <div
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                      expiryEnabled ? "translate-x-5" : ""
                    }`}
                  ></div>
                </button>
              </div>

              {/* Expiry Duration */}
              {expiryEnabled && (
                <div className="ml-7 flex items-center gap-2">
                  <label className="text-sm text-gray-600">Expires in</label>
                  <select
                    value={expiryDays}
                    onChange={(e) => setExpiryDays(Number(e.target.value))}
                    className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={1}>1 day</option>
                    <option value={7}>7 days</option>
                    <option value={30}>30 days</option>
                    <option value={90}>90 days</option>
                  </select>
                </div>
              )}
            </div>
          )}

          {/* Share Link Display */}
          {shareMode !== "private" && (
            <div className="pt-4 border-t border-gray-200">
              <label className="text-sm font-semibold text-gray-700 mb-2 block">
                Share link
              </label>
              <div className="flex gap-2">
                <div className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600 truncate font-mono">
                  {shareUrl}
                </div>
                <button
                  onClick={handleCopyLink}
                  className={`px-4 py-3 rounded-lg font-medium transition-all flex items-center gap-2 ${
                    copied
                      ? "bg-green-50 text-green-600 border border-green-200"
                      : "bg-blue-600 text-white hover:bg-blue-700"
                  }`}
                >
                  {copied ? (
                    <>
                      <Check className="w-4 h-4" />
                      <span className="hidden sm:inline">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      <span className="hidden sm:inline">Copy</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Backend Pending Notice */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex gap-3">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
                <span className="text-amber-600 text-sm font-semibold">!</span>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-amber-900">
                Backend Integration Pending
              </p>
              <p className="text-xs text-amber-700 mt-1">
                Advanced sharing features will be available once the backend API is
                implemented. Current functionality: URL copy only.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleCreateLink}
            disabled={shareMode === "private"}
            className="flex-1 px-4 py-2.5 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {shareMode === "private" ? "Private Mode" : "Create Link"}
          </button>
        </div>
      </div>
    </div>
  );
}
