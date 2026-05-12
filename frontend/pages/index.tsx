import { useEffect } from "react";
import { useRouter } from "next/router";
import { isLoggedIn } from "@/lib/auth";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    if (isLoggedIn()) {
      router.replace("/upload");
    } else {
      router.replace("/login");
    }
  }, [router]);

  return null;
}
