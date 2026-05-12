import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import AuthGuard from "@/components/AuthGuard";
import { getEmotions, selectEmotions, ApiError } from "@/lib/api";
import type { EmotionCandidateSchema } from "@/types";

export default function EmotionsPage() {
  const router = useRouter();
  const { session_id, media_id, media_type } = router.query as Record<string, string>;

  const [candidates, setCandidates] = useState<EmotionCandidateSchema[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!session_id) return;
    loadEmotions();
  }, [session_id]);

  const loadEmotions = async () => {
    try {
      const res = await getEmotions(session_id);
      setCandidates(res.candidates);

      // Pre-select if already selected
      const pre = new Set<string>();
      for (const c of res.candidates) {
        if (c.is_selected) pre.add(c.id);
      }
      setSelected(pre);
    } catch (err) {
      setError("感情選択肢の読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  };

  const toggleEmotion = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSubmit = async () => {
    if (selected.size === 0) {
      setError("最低1つの感情を選択してください");
      return;
    }

    setError("");
    setSubmitting(true);

    try {
      await selectEmotions(session_id, Array.from(selected));
      router.push({
        pathname: "/generate",
        query: { session_id, media_id, media_type },
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("送信に失敗しました");
      }
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <AuthGuard>
        <div className="flex items-center justify-center min-h-[50vh]">
          <div className="animate-spin h-8 w-8 border-4 border-primary-500 border-t-transparent rounded-full" />
        </div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <div className="max-w-lg mx-auto">
        <h1 className="text-2xl font-bold mb-2">感情を選択</h1>
        <p className="text-sm text-gray-500 mb-6">
          メディアから感じた感情を選んでください。複数選択できます。
        </p>

        {error && (
          <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 gap-3">
          {candidates.map((c) => {
            const isSelected = selected.has(c.id);
            return (
              <button
                key={c.id}
                onClick={() => toggleEmotion(c.id)}
                className={`text-left p-4 rounded-xl border-2 transition ${
                  isSelected
                    ? "border-primary-500 bg-primary-50 shadow-sm"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition ${
                      isSelected
                        ? "border-primary-500 bg-primary-500"
                        : "border-gray-300"
                    }`}
                  >
                    {isSelected && (
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-800">{c.emotion_label}</p>
                    <p className="text-sm text-gray-500">{c.emotion_description}</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        <button
          onClick={handleSubmit}
          disabled={submitting || selected.size === 0}
          className="w-full mt-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? "送信中..." : `選択して文章を生成する（${selected.size}個選択中）`}
        </button>
      </div>
    </AuthGuard>
  );
}
