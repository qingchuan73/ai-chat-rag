
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import styles from "../assets/AuthPage.module.css";
import FloatingParticles from "../components/login/Float";
import { message as antdMessage } from "antd";
import { login } from "../api/auth";


function LoginPage() {
    const navigate = useNavigate();
    const [account, setAccount] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e: React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response: any = await login({ account, password });


            const token = response.access_token || response.data?.access_token;
            const username = response.username || response.data?.username;

            if (token) {

                localStorage.setItem("token", token);
                if (username) {
                    localStorage.setItem("username", username);
                }
                antdMessage.success("登录成功");


                navigate("/chat");
            } else {
                antdMessage.error(response.message || "登录验证失败");
            }
        } catch (err: any) {

            const errMsg = err.response?.data?.detail || err.response?.data?.message || "登录失败，请检查您的账号和密码";
            antdMessage.error(errMsg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <FloatingParticles />

            <div className={styles.authCard}>
                <div className={styles.header}>
                    <div className={styles.logo}>DeepSeek GPT</div>
                    <div className={styles.subtitle}>输入您的账号与密码进行登录</div> {/* 2. 修改提示词 */}
                </div>

                <form onSubmit={handleLogin}>
                    <div className={styles.formGroup}>
                        <div className={styles.inputWrapper}>
                            <label className={styles.label}>账号</label> {/* 3. 修改标签为账号 */}
                            <input
                                type="text" // 4. 修改输入类型为 text
                                placeholder="请输入您的账号" // 5. 修改占位符
                                className={styles.inputField}
                                value={account}
                                onChange={(e) => setAccount(e.target.value)}
                                required
                            />
                        </div>
                        <div className={styles.inputWrapper}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <label className={styles.label}>密码</label>
                                <span className={styles.link} style={{ fontSize: '11px', opacity: 0.6 }}>忘记密码？</span>
                            </div>
                            <input
                                type="password"
                                placeholder="请输入密码"
                                className={styles.inputField}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <button type="submit" className={styles.submitBtn} disabled={loading}>
                        {loading ? "安全连接中..." : "登录"}
                    </button>
                </form>

                <div className={styles.footer}>
                    <span>还没有账户？</span>
                    <span className={styles.link} onClick={() => navigate("/register")}>立即创建账户</span>
                </div>
            </div>
        </div>
    );
}

export default LoginPage;
