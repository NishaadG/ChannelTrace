import { StrictMode, lazy, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { DataProvider, Loading } from "./data";
import "./index.css";
import Home from "./pages/Home";

const Research = lazy(() => import("./pages/Research"));
const Analyse = lazy(() => import("./pages/Analyse"));
const Assistant = lazy(() => import("./pages/Assistant"));
const Paper = lazy(() => import("./pages/Paper"));

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <DataProvider>
      <BrowserRouter>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<Home />} />
              <Route path="research" element={<Research />} />
              <Route path="analyse" element={<Analyse />} />
              <Route path="assistant" element={<Assistant />} />
              <Route path="paper" element={<Paper />} />
              <Route path="*" element={<Home />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </DataProvider>
  </StrictMode>,
);
