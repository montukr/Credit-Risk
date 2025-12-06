import React from "react";
import Navbar from "./Navbar";

export default function Layout({ children }) {
  return (
    <div className="app-root">
      <Navbar />
      <main className="app-main">
        <div className="page">{children}</div>
      </main>
    </div>
  );
}
