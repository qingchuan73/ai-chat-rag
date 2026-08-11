// src/pages/registerPage.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom"; // 引入跳转钩子
import styles from "../assets/AuthPage.module.css";
import FloatingParticles from "../components/login/Float"; // 保持与您登录页一致的导入路径
import { message as antdMessage } from "antd";
import { register } from "../api/auth";
function RegisterPage() {
    const [username, setUsername] = useState(""); // 1. 用户名（昵称）
    const [account, setAccount] = useState("");   // 2. 账号（登录ID）
    const [password, setPassword] = useState("");   // 3. 密码
    const [confirmPassword, setConfirmPassword] = useState(""); // 4. 确认密码
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate(); // 初始化跳转

    const handleRegister = async (e: React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoading(true)


        try {
            await register({ username, account, password });
            antdMessage.success("注册成功！请进行登录");


            navigate("/login");


        } catch (err: any) {

            const errMsg = err.response?.data?.detail || err.response?.data?.message || "注册失败，请检查填写内容";
            antdMessage.error(errMsg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.splitContainer}>
            {/* 左侧：表单区 */}
            <div className={styles.leftSection}>
                <div className={styles.authCard} style={{ background: "transparent", border: "none", boxShadow: "none" }}>
                    <div className={styles.header} style={{ textAlign: "left" }}>
                        <div className={styles.logo}>创建账户</div>
                        <div className={styles.subtitle}>请设置您的用户名、登录账号及密码</div>
                    </div>

                    <form onSubmit={handleRegister}>
                        <div className={styles.formGroup}>
                            {/* 用户名（昵称）输入框 */}
                            <div className={styles.inputWrapper}>
                                <label className={styles.label}>用户名</label>
                                <input
                                    type="text"
                                    placeholder="请设置您的昵称"
                                    className={styles.inputField}
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required
                                />
                            </div>
                            {/* 登录账号输入框 */}
                            <div className={styles.inputWrapper}>
                                <label className={styles.label}>账号</label>
                                <input
                                    type="text"
                                    placeholder="请设置您的登录账号"
                                    className={styles.inputField}
                                    value={account}
                                    onChange={(e) => setAccount(e.target.value)}
                                    required
                                />
                            </div>
                            {/* 密码输入框 */}
                            <div className={styles.inputWrapper}>
                                <label className={styles.label}>密码</label>
                                <input
                                    type="password"
                                    placeholder="请设置密码"
                                    className={styles.inputField}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                />
                            </div>
                            {/* 确认密码输入框 */}
                            <div className={styles.inputWrapper}>
                                <label className={styles.label}>确认密码</label>
                                <input
                                    type="password"
                                    placeholder="请再次输入密码确认"
                                    className={styles.inputField}
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <button type="submit" className={styles.submitBtn} disabled={loading}>
                            {loading ? "正在创建账户..." : "注册并登录"}
                        </button>
                    </form>

                    <div className={styles.footer} style={{ justifyContent: "flex-start" }}>
                        <span>已经有账户了？</span>
                        <span className={styles.link} onClick={() => navigate("/login")}>
                            立即登录
                        </span>
                    </div>
                </div>
            </div>

            {/* 右侧：视觉展示栏 */}
            <div className={styles.rightSection}>
                <FloatingParticles />
                <div className={styles.neonGlow}></div>
                <div className={styles.visualWrapper}>
                    <div className={styles.visualTitle}>深度思考，敏捷响应</div>
                    <div className={styles.visualDesc}>
                        基于先进的语言模型构建，为您提供精准、敏捷且富有创意的智能问答与上下文探索体验。
                    </div>
                </div>
            </div>
        </div>
    );
}

export default RegisterPage;
