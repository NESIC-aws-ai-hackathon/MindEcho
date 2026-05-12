import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import AuthGuard from "@/components/AuthGuard";
import {
  getQuestions,
  submitResponses,
  submitFreeText,
  completeQuestions,
  ApiError,
} from "@/lib/api";
import type { ContextQuestionSchema, SubmitResponseItem } from "@/types";

export default function ContextPage() {
  const router = useRouter();
  const { session_id, media_id, media_type } = router.query as Record<string, string>;

  const [questions, setQuestions] = useState<ContextQuestionSchema[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [otherTexts, setOtherTexts] = useState<Record<string, string>>({});
  const [freeText, setFreeText] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!session_id) return;
    loadQuestions();
  }, [session_id]);

  const loadQuestions = async () => {
    try {
      const res = await getQuestions(session_id);
      setQuestions(res.questions);

      // Pre-fill if already answered
      const pre: Record<string, string> = {};
      const preOther: Record<string, string> = {};
      for (const q of res.questions) {
        if (q.selected_choice) pre[q.id] = q.selected_choice;
        if (q.other_text) preOther[q.id] = q.other_text;
      }
      setAnswers(pre);
      setOtherTexts(preOther);
    } catch (err) {
      setError("設問の読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (questionId: string, choice: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: choice }));
  };

  const handleOtherText = (questionId: string, text: string) => {
    setOtherTexts((prev) => ({ ...prev, [questionId]: text }));
  };

  const handleSubmit = async () => {
    setError("");
    setSubmitting(true);

    try {
      // Build responses for answered questions
      const responses: SubmitResponseItem[] = Object.entries(answers).map(
        ([questionId, selectedChoice]) => ({
          question_id: questionId,
          selected_choice: selectedChoice,
          other_text: otherTexts[questionId] || undefined,
        }),
      );

      if (responses.length > 0) {
        await submitResponses(session_id, responses);
      }

      if (freeText.trim()) {
        await submitFreeText(session_id, freeText.trim());
      }

      // Complete questions → generate emotion candidates
      await completeQuestions(session_id);

      router.push({
        pathname: "/emotions",
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
        <h1 className="text-2xl font-bold mb-2">コンテクスト設問</h1>
        <p className="text-sm text-gray-500 mb-6">
          メディアに関する質問に答えて、より的確な文章を生成しましょう。スキップも可能です。
        </p>

        {error && (
          <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {questions.map((q, idx) => (
            <div key={q.id} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <p className="font-medium text-gray-800 mb-3">
                Q{idx + 1}. {q.question_text}
              </p>
              <div className="space-y-2">
                {q.choices.map((c) => (
                  <button
                    key={c.label}
                    onClick={() => handleSelect(q.id, c.label)}
                    className={`w-full text-left px-3 py-2 rounded-lg border text-sm transition ${
                      answers[q.id] === c.label
                        ? "border-primary-500 bg-primary-50 text-primary-700"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <span className="font-medium mr-2">{c.label}.</span>
                    {c.text}
                  </button>
                ))}
              </div>

              {/* "Other" text input */}
              {answers[q.id] === "X" && (
                <input
                  type="text"
                  placeholder="その他の内容を入力"
                  value={otherTexts[q.id] || ""}
                  onChange={(e) => handleOtherText(q.id, e.target.value)}
                  className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              )}
            </div>
          ))}

          {/* Free text */}
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <p className="font-medium text-gray-800 mb-2">自由記述（任意）</p>
            <p className="text-xs text-gray-400 mb-2">
              選択肢にない想いや補足があれば入力してください（最大500文字）
            </p>
            <textarea
              value={freeText}
              onChange={(e) => setFreeText(e.target.value.slice(0, 500))}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
              placeholder="自由に記述してください..."
            />
            <p className="text-xs text-gray-400 text-right mt-1">
              {freeText.length}/500
            </p>
          </div>
        </div>

        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="w-full mt-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? "送信中..." : "次へ進む"}
        </button>
      </div>
    </AuthGuard>
  );
}
