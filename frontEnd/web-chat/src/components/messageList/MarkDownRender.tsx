import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import {oneDark} from 'react-syntax-highlighter/dist/esm/styles/prism'


interface originProps{
    content:string
}

function MarkdownRender({content}:originProps){
    return(
        <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
                code({className,children,...props}){
                    const match=/language-(\w+)/.exec(className || '')
                    const isInline=!className

                    return !isInline && match ?(
                        <SyntaxHighlighter
                            style={oneDark}
                            language={match[1]}
                            PreTag="div"
                        >
                            {String(children).replace(/\n$/,'')}
                        </SyntaxHighlighter>
                    ):(
                        <code className={className} {...props}>
                            {children}
                        </code>
                    )
                }
            }}

        >
            {content}


        </ReactMarkdown>
    )
}

export default MarkdownRender