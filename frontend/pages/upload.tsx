import { useState, useRef, ChangeEvent } from "react";
import { useRouter } from "next/router";
import AuthGuard from "@/components/AuthGuard";
import Toast from "@/components/Toast";
import { createSession, uploadMedia, ApiError } from "@/lib/api";
import type { MediaUploadResponse } from "@/types";

const IMAGE_ACCEPT = ".jpg,.jpeg,.png,.webp,.gif";
const MUSIC_ACCEPT = ".mp3,.wav,.flac,.aac";
const IMAGE_MAX_MB = 10;
const MUSIC_MAX_MB = 50;

type MediaTab = "image" | "music";

export default function UploadPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);

  const [tab, setTab] = useState<MediaTab>("image");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState("");
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  const maxMB = tab === "image" ? IMAGE_MAX_MB : MUSIC_MAX_MB;
  const accept = tab === "image" ? IMAGE_ACCEPT : MUSIC_ACCEPT;

  const handleTabChange = (t: MediaTab) => {
    setTab(t);
    setFile(null);
    setPreview(null);
    setError("");
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;

    if (f.size > maxMB * 1024 * 1024) {
      setError(`ファイルサイズは${maxMB}MB以下にしてください`);
      return;
    }

    setFile(f);
    setError("");

    if (tab === "image") {
      const url = URL.createObjectURL(f);
      setPreview(url);
    } else {
      setPreview(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setError("");
    setUploading(true);

    try {
      setProgress("セッションを作成中...");
      const session = await createSession();

      setProgress("アップロード中...");
      const result: MediaUploadResponse = await uploadMedia(
        session.id,
        file,
        tab,
      );

      setProgress("解析完了！");
      setToast("解析が完了しました");

      // Navigate to context page with session info
      setTimeout(() => {
        router.push({
          pathname: "/context",
          query: {
            session_id: session.id,
            media_id: result.media_file.id,
            media_type: tab,
          },
        });
      }, 1000);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("アップロードに失敗しました。もう一度お試しください。");
      }
      setUploading(false);
      setProgress("");
    }
  };

  return (
    <AuthGuard>
      <div className="max-w-lg mx-auto">
        <h1 className="text-2xl font-bold mb-6">メディアをアップロード</h1>

        {/* Tab */}
        <div className="flex border-b border-gray-200 mb-6">
          {(["image", "music"] as MediaTab[]).map((t) => (
            <button
              key={t}
              onClick={() => handleTabChange(t)}
              className={`flex-1 py-2 text-sm font-medium border-b-2 transition ${
                tab === t
                  ? "border-primary-600 text-primary-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {t === "image" ? "画像" : "音楽"}
            </button>
          ))}
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {/* Drop zone */}
        {!uploading && (
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-primary-400 transition"
          >
            <input
              ref={fileRef}
              type="file"
              accept={accept}
              onChange={handleFileChange}
              className="hidden"
            />

            {file ? (
              <div className="space-y-3">
                {preview && tab === "image" && (
                  <img
                    src={preview}
                    alt="preview"
                    className="mx-auto max-h-48 rounded-lg object-contain"
                  />
                )}
                {tab === "music" && (
                  <div className="text-4xl">🎵</div>
                )}
                <p className="text-sm text-gray-700">{file.name}</p>
                <p className="text-xs text-gray-400">
                  {(file.size / 1024 / 1024).toFixed(1)} MB
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="text-4xl">{tab === "image" ? "📷" : "🎵"}</div>
                <p className="text-gray-500">
                  クリックして{tab === "image" ? "画像" : "音楽"}ファイルを選択
                </p>
                <p className="text-xs text-gray-400">
                  {tab === "image"
                    ? "JPEG, PNG, WebP, GIF（最大10MB）"
                    : "MP3, WAV, FLAC, AAC（最大50MB）"}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Upload progress */}
        {uploading && (
          <div className="text-center py-12 space-y-4">
            <div className="animate-spin h-10 w-10 border-4 border-primary-500 border-t-transparent rounded-full mx-auto" />
            <p className="text-gray-600">{progress}</p>
          </div>
        )}

        {/* Upload button */}
        {file && !uploading && (
          <button
            onClick={handleUpload}
            className="w-full mt-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium"
          >
            アップロードして解析する
          </button>
        )}
      </div>

      {toast && <Toast message={toast} onClose={() => setToast("")} />}
    </AuthGuard>
  );
}
