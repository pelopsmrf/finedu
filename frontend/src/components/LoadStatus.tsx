import { Link } from "react-router-dom";
import { LoadState } from "../useLoad";

/** Shows "loading" or an error with a retry button; renders nothing once data is here. */
export default function LoadStatus({ state }: { state: LoadState<unknown> }) {
  if (state.loading && state.data === null) {
    return <p className="muted">Загрузка…</p>;
  }
  if (state.notFound) {
    return (
      <div className="notice">
        <p>Такой страницы нет — возможно, её убрали или ссылка устарела.</p>
        <Link to="/" className="btn">
          К темам
        </Link>
      </div>
    );
  }
  if (state.error) {
    return (
      <div className="notice notice--error">
        <p>Не получилось загрузить. Проверь интернет и попробуй ещё раз.</p>
        <button className="btn" onClick={state.reload}>
          Повторить
        </button>
      </div>
    );
  }
  return null;
}
