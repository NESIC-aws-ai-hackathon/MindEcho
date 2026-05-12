import { useState } from "react";
import { useRouter } from "next/router";
import AuthGuard from "@/components/AuthGuard";
import Toast from "@/components/Toast";
import { deleteAccount, ApiError } from "@/lib/api";
import { removeToken } from "@/lib/auth";

export default function SettingsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  const handleDeleteAccount = async () => {
    if (
      !confirm(
        "アカウントと全関連データを完全に削除します。この操作は取り消せません。本当に削除しますか？",
      )
    ) {
      return;
    }

    // Double confirmation
    if (!confirm("最終確認：本当にアカウントを削除しますか？")) {
      return;
    }

    setError("");
    setLoading(true);

    try {
      await deleteAccount();
      removeToken();
      router.push("/login");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("アカウント削除に失敗しました");
      }
      setLoading(false);
    }
  };

  return (
    <AuthGuard>
      <div className="max-w-lg mx-auto">
        <h1 className="text-2xl font-bold mb-8">設定</h1>

        {error && (
          <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {/* Danger zone */}
        <div className="border border-red-200 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-red-600 mb-2">危険な操作</h2>
          <p className="text-sm text-gray-600 mb-4">
            アカウントを削除すると、メディアファイル・生成履歴・ユーザー情報を含む全てのデータが完全に削除されます。この操作は取り消すことができません。
          </p>
          <button
            onClick={handleDeleteAccount}
            disabled={loading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "削除中..." : "アカウントを削除する"}
          </button>
        </div>
      </div>

      {toast && <Toast message={toast} onClose={() => setToast("")} />}
    </AuthGuard>
  );
}
