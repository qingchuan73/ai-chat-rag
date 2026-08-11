import axios from "axios";
import { API_BASE_URL } from "./config";

const request=axios.create({
    baseURL: API_BASE_URL,
    timeout:10000
})

request.interceptors.request.use(
    config=>{
        const token=localStorage.getItem("token")
        if(token){
            config.headers.Authorization=
            `Bearer ${token}`
        }
         return config
    }

   
)

request.interceptors.response.use(
    response => {
        return response.data;
    },
    error => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem("token");
        }
        return Promise.reject(error);
    }
);

export default request
