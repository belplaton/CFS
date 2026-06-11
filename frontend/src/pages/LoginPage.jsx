import { Navigate, Link, useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";

import { useI18n } from "@/components/app/I18nProvider";
import AuthShell from "@/components/auth/AuthShell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/auth-store";

function LoginPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const login = useAuthStore((state) => state.login);
  const isLoading = useAuthStore((state) => state.isLoading);
  const error = useAuthStore((state) => state.error);
  const clearError = useAuthStore((state) => state.clearError);

  if (isAuthenticated) {
    return <Navigate replace to="/app/files" />;
  }

  const from = location.state?.from?.pathname ?? "/app/files";
  const notice = location.state?.notice ?? "";

  useEffect(() => {
    clearError();
  }, [clearError]);

  const handleLogin = async (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const email = formData.get("email")?.toString().trim() ?? "";
    const password = formData.get("password")?.toString() ?? "";

    const result = await login(email, password);

    if (result.success) {
      navigate(from, { replace: true });
    }
  };

  return (
    <AuthShell
      description={t("login.description")}
      eyebrow={t("login.eyebrow")}
      footer={
        <span>
          {t("login.noAccount")}{" "}
          <Link
            className="font-medium underline underline-offset-4"
            to="/register"
          >
            {t("login.create")}
          </Link>
        </span>
      }
      title={t("login.title")}
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">{t("login.cardTitleSignIn")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          <form className="space-y-4" onSubmit={handleLogin}>
            {notice ? (
              <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-foreground">
                {notice}
              </div>
            ) : null}
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="login-email">
                Email
              </label>
              <Input
                id="login-email"
                name="email"
                type="email"
                required
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-4">
                <label
                  className="text-sm font-medium"
                  htmlFor="login-password"
                >
                  {t("common.password")}
                </label>
                <Link
                  className="text-sm underline underline-offset-4"
                  to="/forgot-password"
                >
                  {t("login.forgotPassword")}
                </Link>
              </div>
              <Input
                id="login-password"
                name="password"
                type="password"
                required
              />
            </div>

            {error ? (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {error}
              </div>
            ) : null}

            <Button
              className="mt-2 w-full py-6 text-base"
              type="submit"
              disabled={isLoading}
            >
              {isLoading ? t("common.loading") : t("login.signIn")}
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  );
}

export default LoginPage;
