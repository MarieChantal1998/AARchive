import Link from "next/link";

export function Logo() {
  return (
    <Link href="/" className="logo" aria-label="AARchive home">
      <span className="logo-mark" aria-hidden="true"><i /><i /><i /></span>
      <span>AAR<span>chive</span></span>
    </Link>
  );
}

