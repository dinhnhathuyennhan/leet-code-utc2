"use client"

import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function handleLogin() {
    toast(`Email: ${email} - Mật khẩu: ${password}`);
  }

  return (
    <Card className="w-full max-w-sm">
      <CardHeader><CardTitle>Đăng nhập</CardTitle></CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="password">Mật khẩu</Label>
          <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <Button type="submit" onClick={handleLogin}>Đăng nhập</Button>
      </CardContent>
    </Card>
  )
}
