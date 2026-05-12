import Link from "next/link";
import { useRouter } from "next/router";
import { isLoggedIn, removeToken } from "@/lib/auth";

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const router = useRouter();
  const loggedIn = isLoggedIn();

  const handleLogout = () => {
    removeToken();
    router.push("/login");
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-primary-600">
            MindEcho
          </Link>
          {loggedIn && (
            <nav className="flex items-center gap-4 text-sm">
              <Link href="/upload" className="text-gray-600 hover:text-primary-600">
                新規作成
              </Link>
              <Link href="/history" className="text-gray-600 hover:text-primary-600">
                履歴
              </Link>
              <Link href="/settings" className="text-gray-600 hover:text-primary-600">
                設定
              </Link>
              <button
                onClick={handleLogout}
                className="text-gray-400 hover:text-red-500"
              >
                ログアウト
              </button>
            </nav>
          )}
        </div>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-8">
        {children}
      </main>

      <footer className="border-t border-gray-100 py-4 text-center text-xs text-gray-400">
        &copy; 2026 MindEcho
      </footer>
    </div>
  );
}
