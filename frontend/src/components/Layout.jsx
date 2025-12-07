import React from "react";

export default function Layout({ children }) {
  return (
    <div className="app-root">
      <main className="app-main">
        <div className="page">{children}</div>
      </main>
    </div>
  );
}
