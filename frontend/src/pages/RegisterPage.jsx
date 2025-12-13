// import React, { useState } from "react";
// import { Link, useNavigate } from "react-router-dom";
// import { useAuth } from "../AuthContext";
// import api from "../api";

// export default function RegisterPage() {
//   const { register } = useAuth();
//   const nav = useNavigate();

//   const [form, setForm] = useState({
//     username: "",
//     email: "",
//     password: "",
//     phone: "",
//   });

//   const [otp, setOtp] = useState("");
//   const [otpSent, setOtpSent] = useState(false);
//   const [otpVerified, setOtpVerified] = useState(false);

//   const [loading, setLoading] = useState(false);
//   const [otpLoading, setOtpLoading] = useState(false);
//   const [error, setError] = useState("");
//   const [otpError, setOtpError] = useState("");

//   const onChange = (e) => {
//     setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
//   };

//   // -------------------------------------------
//   // SEND OTP
//   // -------------------------------------------
//   const sendOtp = async () => {
//     setOtpError("");
//     if (!form.phone) {
//       setOtpError("Enter phone number first.");
//       return;
//     }
//     setOtpLoading(true);

//     try {
//       await api.post("/auth/whatsapp/send_otp", { phone: form.phone });
//       setOtpSent(true);
//     } catch (err) {
//       setOtpError("Failed to send OTP");
//       console.error(err);
//     } finally {
//       setOtpLoading(false);
//     }
//   };

//   // -------------------------------------------
//   // VERIFY OTP
//   // -------------------------------------------
//   const verifyOtp = async () => {
//     setOtpError("");
//     if (!otp) {
//       setOtpError("Enter the OTP");
//       return;
//     }

//     setOtpLoading(true);
//     try {
//       const res = await api.post("/auth/whatsapp/verify_otp", {
//         phone: form.phone,
//         code: otp,
//         username: form.username, // backend only needs it for new users
//       });

//       if (res.data?.detail === "Username required") {
//         // Should not happen during registration flow
//         setOtpError("Username missing");
//       } else {
//         setOtpVerified(true);
//       }
//     } catch (err) {
//       setOtpError("Invalid or expired OTP");
//     } finally {
//       setOtpLoading(false);
//     }
//   };

//   // -------------------------------------------
//   // SUBMIT REGISTRATION (ONLY IF OTP VERIFIED)
//   // -------------------------------------------
//   const onSubmit = async (e) => {
//     e.preventDefault();
//     setError("");

//     if (!otpVerified) {
//       setError("Please verify your phone number first.");
//       return;
//     }

//     setLoading(true);
//     try {
//       await register(form);
//       nav("/");
//     } catch (err) {
//       const detail = err?.response?.data?.detail;
//       if (Array.isArray(detail)) {
//         setError(detail[0]?.msg || "Invalid input");
//       } else if (typeof detail === "string") {
//         setError(detail);
//       } else {
//         setError("Registration failed. Please check your input.");
//       }
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="app-root">
//       <div className="auth-card">
//         <h1>Create HDFC Credit Card account</h1>
//         <p className="page-caption">
//           Password can be as short as 4 characters for this sandbox.
//         </p>

//         {error && <p className="error-text">{error}</p>}

//         <form onSubmit={onSubmit}>
//           {/* Username */}
//           <div>
//             <label>
//               <span>Username</span>
//               <input
//                 name="username"
//                 value={form.username}
//                 onChange={onChange}
//                 placeholder="jane.doe"
//               />
//             </label>
//           </div>

//           {/* Email */}
//           <div>
//             <label>
//               <span>Email</span>
//               <input
//                 name="email"
//                 type="email"
//                 value={form.email}
//                 onChange={onChange}
//                 placeholder="you@example.com"
//               />
//             </label>
//           </div>

//           {/* Phone + OTP side-by-side */}
//           <div>
//             <label>
//               <span>Phone (WhatsApp)</span>
//               <div style={{ display: "flex", gap: "8px" }}>
//                 <input
//                   name="phone"
//                   value={form.phone}
//                   onChange={onChange}
//                   placeholder="91XXXXXXXXXX"
//                   disabled={otpVerified}
//                   style={{ flex: 1 }}
//                 />

//                 {!otpVerified && (
//                   <button
//                     type="button"
//                     className="pill-btn"
//                     onClick={sendOtp}
//                     disabled={otpLoading}
//                   >
//                     {otpLoading ? "Sending..." : "Send OTP"}
//                   </button>
//                 )}

//                 {otpVerified && (
//                   <span style={{ color: "green", fontWeight: "bold" }}>
//                     ✓ Verified
//                   </span>
//                 )}
//               </div>
//             </label>

//             {/* OTP input */}
//             {otpSent && !otpVerified && (
//               <div style={{ marginTop: 10 }}>
//                 <div style={{ display: "flex", gap: "8px" }}>
//                   <input
//                     value={otp}
//                     onChange={(e) => setOtp(e.target.value)}
//                     placeholder="Enter OTP"
//                     style={{ flex: 1 }}
//                   />
//                   <button
//                     type="button"
//                     className="pill-btn"
//                     onClick={verifyOtp}
//                     disabled={otpLoading}
//                   >
//                     {otpLoading ? "Verifying..." : "Verify"}
//                   </button>
//                 </div>
//                 {otpError && <p className="error-text">{otpError}</p>}
//               </div>
//             )}
//           </div>

//           {/* Password */}
//           <div>
//             <label>
//               <span>Password (min 4 chars)</span>
//               <input
//                 name="password"
//                 type="password"
//                 value={form.password}
//                 onChange={onChange}
//                 placeholder="••••"
//               />
//             </label>
//           </div>

//           <button type="submit" disabled={loading}>
//             {loading ? "Creating..." : "Create account"}
//           </button>
//         </form>

//         <p className="muted" style={{ marginTop: 10 }}>
//           Already have an account? <Link to="/login">Sign in</Link>
//         </p>
//       </div>
//     </div>
//   );
// }


import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import api from "../api";

export default function RegisterPage() {
  const { register } = useAuth();
  const nav = useNavigate();

  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    phone: "",
  });

  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);

  const [loading, setLoading] = useState(false);
  const [otpLoading, setOtpLoading] = useState(false);
  const [error, setError] = useState("");
  const [otpError, setOtpError] = useState("");

  const onChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  // -------------------------------------------
  // SEND OTP
  // -------------------------------------------
  const sendOtp = async () => {
    setOtpError("");
    if (!form.phone) {
      setOtpError("Enter phone number first.");
      return;
    }
    setOtpLoading(true);

    try {
      await api.post("/auth/whatsapp/send_otp", { phone: form.phone });
      setOtpSent(true);
    } catch (err) {
      if (!err?.response) {
        setOtpError("Network error. Could not reach the server.");
      } else {
        setOtpError("Failed to send OTP");
      }
      console.error(err);
    } finally {
      setOtpLoading(false);
    }
  };

  // -------------------------------------------
  // VERIFY OTP
  // -------------------------------------------
  const verifyOtp = async () => {
    setOtpError("");
    if (!otp) {
      setOtpError("Enter the OTP");
      return;
    }

    setOtpLoading(true);
    try {
      const res = await api.post("/auth/whatsapp/verify_otp", {
        phone: form.phone,
        code: otp,
        username: form.username, // backend only needs it for new users
      });

      if (res.data?.detail === "Username required") {
        // Should not happen during registration flow
        setOtpError("Username missing");
      } else {
        setOtpVerified(true);
      }
    } catch (err) {
      if (!err?.response) {
        setOtpError("Network error. Could not reach the server.");
      } else {
        setOtpError("Invalid or expired OTP");
      }
    } finally {
      setOtpLoading(false);
    }
  };

  // -------------------------------------------
  // SUBMIT REGISTRATION (ONLY IF OTP VERIFIED)
  // -------------------------------------------
  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!otpVerified) {
      setError("Please verify your phone number first.");
      return;
    }

    setLoading(true);
    try {
      await register(form);
      nav("/");
    } catch (err) {
      if (!err?.response) {
        setError("Network error. Could not reach the server.");
      } else {
        const detail = err.response?.data?.detail;
        if (Array.isArray(detail)) {
          setError(detail[0]?.msg || "Invalid input");
        } else if (typeof detail === "string") {
          setError(detail);
        } else {
          setError("Registration failed. Please check your input.");
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-root">
      <div className="auth-card">
        <h1>Create HDFC Credit Card account</h1>
        <p className="page-caption">
          Password can be as short as 4 characters for this sandbox.
        </p>

        {error && <p className="error-text">{error}</p>}

        <form onSubmit={onSubmit}>
          {/* Username */}
          <div>
            <label>
              <span>Username</span>
              <input
                name="username"
                value={form.username}
                onChange={onChange}
                placeholder="jane.doe"
              />
            </label>
          </div>

          {/* Email */}
          <div>
            <label>
              <span>Email</span>
              <input
                name="email"
                type="email"
                value={form.email}
                onChange={onChange}
                placeholder="you@example.com"
              />
            </label>
          </div>

          {/* Phone + OTP side-by-side */}
          <div>
            <label>
              <span>Phone (WhatsApp)</span>
              <div style={{ display: "flex", gap: "8px" }}>
                <input
                  name="phone"
                  value={form.phone}
                  onChange={onChange}
                  placeholder="91XXXXXXXXXX"
                  disabled={otpVerified}
                  style={{ flex: 1 }}
                />

                {!otpVerified && (
                  <button
                    type="button"
                    className="pill-btn"
                    onClick={sendOtp}
                    disabled={otpLoading}
                  >
                    {otpLoading ? "Sending..." : "Send OTP"}
                  </button>
                )}

                {otpVerified && (
                  <span style={{ color: "green", fontWeight: "bold" }}>
                    ✓ Verified
                  </span>
                )}
              </div>
            </label>

            {/* OTP input */}
            {otpSent && !otpVerified && (
              <div style={{ marginTop: 10 }}>
                <div style={{ display: "flex", gap: "8px" }}>
                  <input
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="Enter OTP"
                    style={{ flex: 1 }}
                  />
                  <button
                    type="button"
                    className="pill-btn"
                    onClick={verifyOtp}
                    disabled={otpLoading}
                  >
                    {otpLoading ? "Verifying..." : "Verify"}
                  </button>
                </div>
                {otpError && <p className="error-text">{otpError}</p>}
              </div>
            )}
          </div>

          {/* Password */}
          <div>
            <label>
              <span>Password (min 4 chars)</span>
              <input
                name="password"
                type="password"
                value={form.password}
                onChange={onChange}
                placeholder="••••"
              />
            </label>
          </div>

          <button type="submit" disabled={loading}>
            {loading ? "Creating..." : "Create account"}
          </button>
        </form>

        <p className="muted" style={{ marginTop: 10 }}>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
