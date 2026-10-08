// ygo interop harness: applies yjs@13-generated wire fixtures into a ygo doc
// and re-encodes state for JS-side reverse verification. ACs pre-registered
// in src/sandbox/ygo-poc/README.md (AC-YG1..YG5 go-side stages).
package main

import (
	"fmt"
	"os"

	"github.com/Deln0r/ygo"
)

const fx = "../data/fixtures"
const out = "../data/out"

func mustRead(p string) []byte {
	b, err := os.ReadFile(p)
	if err != nil {
		panic(err)
	}
	return b
}

func mustWrite(p string, b []byte) {
	if err := os.WriteFile(p, b, 0o644); err != nil {
		panic(err)
	}
}

func main() {
	if err := os.MkdirAll(out, 0o755); err != nil {
		panic(err)
	}

	// AC-YG1: yjs V1 update applies into a ygo doc (subset check here;
	// full semantic compare happens JS-side on the reverse round-trip).
	doc := ygo.NewDoc()
	if err := ygo.ApplyUpdate(doc, mustRead(fx+"/fx1-v1.bin")); err != nil {
		fmt.Println("FAIL AC-YG1 v1 apply:", err)
		os.Exit(1)
	}
	m := ygo.NewMap(doc, "settings")
	theme, _ := m.Get("theme").(string)
	x := fmt.Sprintf("%v", m.Get("x"))
	count := fmt.Sprintf("%v", m.Get("count"))
	arr := ygo.NewArray(doc, "chatlog")
	txt := ygo.NewText(doc, "canvas").String()
	if theme != "dark" || x != "123.456" || count != "8" || txt != "ello world!" || arr.Len() != 2 {
		fmt.Printf("FAIL AC-YG1 state mismatch: theme=%q x=%q count=%q text=%q arrlen=%d\n", theme, x, count, txt, arr.Len())
		os.Exit(1)
	}
	fmt.Println("PASS AC-YG1 js-v1 -> ygo apply, state subset matches (theme/x/count/text/arrlen)")
	mustWrite(out+"/sv-go-a.bin", ygo.EncodeStateVector(doc))
	mustWrite(out+"/go-state-a-v1.bin", ygo.EncodeStateAsUpdate(doc))

	// AC-YG3 (go side): yjs V2 update applies into a fresh ygo doc.
	doc2 := ygo.NewDoc()
	if err := ygo.ApplyUpdateV2(doc2, mustRead(fx+"/fx1-v2.bin")); err != nil {
		fmt.Println("FAIL AC-YG3 v2 apply:", err)
		os.Exit(1)
	}
	m2 := ygo.NewMap(doc2, "settings")
	theme2, _ := m2.Get("theme").(string)
	txt2 := ygo.NewText(doc2, "canvas").String()
	if theme2 != "dark" || txt2 != "ello world!" {
		fmt.Printf("FAIL AC-YG3 v2 state mismatch: theme=%q text=%q\n", theme2, txt2)
		os.Exit(1)
	}
	fmt.Println("PASS AC-YG3-pre js-v2 -> ygo applyV2, state matches")
	mustWrite(out+"/go-state-a-v2.bin", ygo.EncodeStateAsUpdateV2(doc2))

	// AC-YG5 (go side): merge two concurrent yjs updates, re-encode for JS check.
	docM := ygo.NewDoc()
	if err := ygo.ApplyUpdate(docM, mustRead(fx+"/fxA-v1.bin")); err != nil {
		fmt.Println("FAIL AC-YG5 applyA:", err)
		os.Exit(1)
	}
	if err := ygo.ApplyUpdate(docM, mustRead(fx+"/fxB-v1.bin")); err != nil {
		fmt.Println("FAIL AC-YG5 applyB:", err)
		os.Exit(1)
	}
	mustWrite(out+"/go-merge.bin", ygo.EncodeStateAsUpdate(docM))
	fmt.Println("PASS AC-YG5-pre ygo merged concurrent yjs updates, re-encoded")

	fmt.Println("GO-HARNESS OK")
}
