import Image from "next/image";

/** 5 ngôn ngữ hệ thống hỗ trợ chấm bài. Icon đặt trong `public/images/lang/`. */
const LANGUAGES = [
  { name: "C", icon: "/images/c.svg" },
  { name: "C++", icon: "/images/cpp.svg" },
  { name: "Java", icon: "/images/java.svg" },
  { name: "JavaScript", icon: "/images/javascript.svg" },
  { name: "Python", icon: "/images/python.svg" },
] as const;

export function LanguageStrip({...props}) {
  return (
    <div className="space-y-4 max-[700px]:space-y-2">
      <div className={`${props.hiddenText ? 'hidden' : ''} flex items-center gap-3`}>
        <span className="h-px flex-1 bg-[#94A3B8]" />
        <span className="text-[12px] font-medium uppercase tracking-widest text-slate-400">
          Với các ngôn ngữ
        </span>
        <span className="h-px flex-1 bg-[#94A3B8]" />
      </div>

      <ul className={`flex ${props.width == 60 ? 'justify-start' : 'justify-center'} items-center  gap-6 max-[700px]:gap-3`}>
        {LANGUAGES.map((language) => (
          <li key={language.name}>
            <Image
              src={language.icon}
              alt={language.name}
              title={language.name}
              width={props.width || 40}
              height={props.height || 40}
              className=" max-[700px]:size-7"
            />
          </li>
        ))}
      </ul>
    </div>
  );
}