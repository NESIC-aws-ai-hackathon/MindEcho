import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import AuthGuard from "@/components/AuthGuard";
import Toast from "@/components/Toast";
import {
  getFormats,
  generateText,
  getGeneratedText,
  getMediaDetail,
  ApiError,
} from "@/lib/api";
import type {
  FormatInfo,
  GeneratedTextSchema,
  ImageAnalysis,
  MusicAnalysis,
} from "@/types";

export default function GeneratePage() {
  const router = useRouter();
  const { session_id, media_id, media_type } = router.query as Record<string, string>;

  const [formats, setFormats] = useState<FormatInfo[]>([]);
  const [selectedFormat, setSelectedFormat] = useState("");
  const [result, setResult] = useState<GeneratedTextSchema | null>(null);
  const [imageAnalysis, setImageAnalysis] = useState<ImageAnalysis | null>(null);
  const [musicAnalysis, setMusicAnalysis] = useState<MusicAnalysis | null>(null);
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  useEffect(() => {
    if (!session_id) return;
    init();
  }, [session_id]);

  const init = async () => {
    try {
      const [fmts, mediaDetail] = await Promise.all([
        getFormats(),
        media_id ? getMediaDetail(media_id) : null,
      ]);

      setFormats(fmts.formats);
      const defaultFmt = fmts.formats.find((f) => f.is_default) || fmts.formats[0];
      if (defaultFmt) setSelectedFormat(defaultFmt.id);

      if (mediaDetail) {
        setImageAnalysis(mediaDetail.image_analysis);
        setMusicAnalysis(mediaDetail.music_analysis);
      }

      // Check if already generated
      try {
        const existing = await getGeneratedText(session_id);
        setResult(existing);
        setSelectedFormat(existing.output_format);
      } catch {
        // No existing text — that's fine
      }
    } catch {
      setError("初期化に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setError("");
    setGenerating(true);

    try {
      const res = await generateText(session_id, selectedFormat);
      setResult(res);
      setToast(res.generation_count === 1 ? "文章を生成しました" : "文章を再生成しました");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("生成に失敗しました");
      }
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = async () => {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.generated_content);
      setToast("コピーしました");
    } catch {
      setToast("コピーに失敗しました");
    }
  };

  const handleShare = async () => {
    if (!result) return;
    const text = result.generated_content;

    if (navigator.share) {
      try {
        await navigator.share({ text });
        return;
      } catch {
        // User cancelled or not supported
      }
    }

    // Fallback: X/Twitter Web Intent
    const encoded = encodeURIComponent(text);
    window.open(
      `https://twitter.com/intent/tweet?text=${encoded}`,
      "_blank",
      "noopener,noreferrer",
    );
  };

  const currentFormat = formats.find((f) => f.id === selectedFormat);

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
        <h1 className="text-2xl font-bold mb-6">文章生成</h1>

        {error && (
          <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {/* Format selection */}
        <div className="mb-6">
          <p className="text-sm font-medium text-gray-700 mb-3">出力形式を選択</p>
          <div className="space-y-2">
            {formats.map((f) => (
              <button
                key={f.id}
                onClick={() => setSelectedFormat(f.id)}
                className={`w-full text-left p-3 rounded-lg border-2 transition ${
                  selectedFormat === f.id
                    ? "border-primary-500 bg-primary-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <div className="flex justify-between items-center">
                  <span className="font-medium text-gray-800">{f.name}</span>
                  <span className="text-xs text-gray-400">
                    {f.min_chars}〜{f.max_chars}文字
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">{f.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Generate button */}
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="w-full py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {generating
            ? "生成中..."
            : result
              ? `再生成する（${result.generation_count}/10）`
              : "文章を生成する"}
        </button>

        {/* Result */}
        {result && (
          <div className="mt-6 space-y-4">
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium px-2 py-1 bg-primary-100 text-primary-700 rounded">
                  {currentFormat?.name || result.output_format}
                </span>
                <span className="text-xs text-gray-400">
                  {result.generated_content.length}文字
                </span>
              </div>
              <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">
                {result.generated_content}
              </p>
            </div>

            {/* Action buttons */}
            <div className="flex gap-2">
              <button
                onClick={handleCopy}
                className="flex-1 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium"
              >
                コピー
              </button>
              <button
                onClick={handleShare}
                className="flex-1 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium"
              >
                シェア
              </button>
            </div>

            {/* Analysis result (bonus) */}
            {(imageAnalysis || musicAnalysis) && (
              <details className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                <summary className="text-sm font-medium text-gray-600 cursor-pointer">
                  AI解析リザルト
                </summary>
                <div className="mt-3 text-sm text-gray-600 space-y-1">
                  {imageAnalysis && (
                    <>
                      <p><span className="font-medium">色彩:</span> {imageAnalysis.colors.join(", ")}</p>
                      <p><span className="font-medium">構図:</span> {imageAnalysis.composition}</p>
                      <p><span className="font-medium">雰囲気:</span> {imageAnalysis.atmosphere}</p>
                      <p><span className="font-medium">被写体:</span> {imageAnalysis.subjects.join(", ")}</p>
                      <p><span className="font-medium">印象:</span> {imageAnalysis.emotional_impression}</p>
                    </>
                  )}
                  {musicAnalysis && (
                    <>
                      {musicAnalysis.title && (
                        <p><span className="font-medium">タイトル:</span> {musicAnalysis.title}</p>
                      )}
                      {musicAnalysis.artist && (
                        <p><span className="font-medium">アーティスト:</span> {musicAnalysis.artist}</p>
                      )}
                      <p><span className="font-medium">テンポ:</span> {musicAnalysis.tempo}</p>
                      <p><span className="font-medium">リズム:</span> {musicAnalysis.rhythm}</p>
                      <p><span className="font-medium">雰囲気:</span> {musicAnalysis.mood}</p>
                      <p><span className="font-medium">印象:</span> {musicAnalysis.emotional_impression}</p>
                    </>
                  )}
                </div>
              </details>
            )}

            {/* New session */}
            <button
              onClick={() => router.push("/upload")}
              className="w-full py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 text-sm"
            >
              新しいメディアで作成する
            </button>
          </div>
        )}
      </div>

      {toast && <Toast message={toast} onClose={() => setToast("")} />}
    </AuthGuard>
  );
}
