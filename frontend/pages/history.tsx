import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import AuthGuard from "@/components/AuthGuard";
import Toast from "@/components/Toast";
import { listSessions, deleteSession, ApiError } from "@/lib/api";
import type { SessionResponse } from "@/types";

const STATUS_LABELS: Record<string, string> = {
  created: "作成済み",
  media_uploaded: "アップロード済み",
  questions_generated: "設問生成済み",
  questions_answered: "回答済み",
  emotions_selected: "感情選択済み",
  generated: "生成済み",
  completed: "完了",
};

export default function HistoryPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<SessionResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    loadSessions();
  }, [page]);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const res = await listSessions(page);
      setSessions(res.items);
      setTotal(res.total);
    } catch {
      setError("履歴の読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("このセッションを削除しますか？この操作は取り消せません。")) return;

    setDeleting(id);
    try {
      await deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      setTotal((prev) => prev - 1);
      setToast("セッションを削除しました");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("削除に失敗しました");
      }
    } finally {
      setDeleting(null);
    }
  };

  const handleResume = (s: SessionResponse) => {
    const query: Record<string, string> = { session_id: s.id };
    if (s.media_type) query.media_type = s.media_type;

    // Navigate based on status
    switch (s.status) {
      case "created":
        router.push("/upload");
        return;
      case "media_uploaded":
      case "questions_generated":
        router.push({ pathname: "/context", query });
        return;
      case "questions_answered":
        router.push({ pathname: "/emotions", query });
        return;
      case "emotions_selected":
      case "generated":
      case "completed":
        router.push({ pathname: "/generate", query });
        return;
      default:
        router.push("/upload");
    }
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <AuthGuard>
      <div className="max-w-lg mx-auto">
        <h1 className="text-2xl font-bold mb-6">セッション履歴</h1>

        {error && (
          <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin h-8 w-8 border-4 border-primary-500 border-t-transparent rounded-full" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <p className="text-lg mb-2">履歴がありません</p>
            <button
              onClick={() => router.push("/upload")}
              className="text-primary-600 hover:underline text-sm"
            >
              最初のメディアをアップロードする
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((s) => (
              <div
                key={s.id}
                className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 flex items-center justify-between"
              >
                <button
                  onClick={() => handleResume(s)}
                  className="flex-1 text-left"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm">
                      {s.media_type === "image" ? "📷" : s.media_type === "music" ? "🎵" : "📄"}
                    </span>
                    <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                      {STATUS_LABELS[s.status] || s.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400">
                    {new Date(s.created_at).toLocaleString("ja-JP")}
                  </p>
                </button>

                <button
                  onClick={() => handleDelete(s.id)}
                  disabled={deleting === s.id}
                  className="text-gray-400 hover:text-red-500 p-2 disabled:opacity-50"
                  title="削除"
                >
                  {deleting === s.id ? "..." : "✕"}
                </button>
              </div>
            ))}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center gap-2 pt-4">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 text-sm border rounded disabled:opacity-30"
                >
                  前へ
                </button>
                <span className="px-3 py-1 text-sm text-gray-500">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1 text-sm border rounded disabled:opacity-30"
                >
                  次へ
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {toast && <Toast message={toast} onClose={() => setToast("")} />}
    </AuthGuard>
  );
}
