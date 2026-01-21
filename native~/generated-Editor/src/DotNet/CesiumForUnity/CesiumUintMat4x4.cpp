#include <DotNet/CesiumForUnity/CesiumUintMat4x4.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/CesiumUintVec4.h>
#include <cstdint>

namespace DotNet::CesiumForUnity {
struct CesiumUintVec4;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintMat4x4;
}

namespace DotNet::CesiumForUnity {

void (*CesiumUintMat4x4::Construct_UoXJ1ZrrVKjTtIO7sqwAHQ)(const ::DotNet::CesiumForUnity::CesiumUintVec4* v0, const ::DotNet::CesiumForUnity::CesiumUintVec4* v1, const ::DotNet::CesiumForUnity::CesiumUintVec4* v2, const ::DotNet::CesiumForUnity::CesiumUintVec4* v3, ::DotNet::CesiumForUnity::CesiumUintMat4x4* pReturnValue, void** reinteropException) = nullptr;


CesiumUintMat4x4 CesiumUintMat4x4::Construct(const ::DotNet::CesiumForUnity::CesiumUintVec4& v0, const ::DotNet::CesiumForUnity::CesiumUintVec4& v1, const ::DotNet::CesiumForUnity::CesiumUintVec4& v2, const ::DotNet::CesiumForUnity::CesiumUintVec4& v3)
{
    void* reinteropException = nullptr;
    CesiumUintMat4x4 result;
    Construct_UoXJ1ZrrVKjTtIO7sqwAHQ(&v0, &v1, &v2, &v3, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUintMat4x4::Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumUintMat4x4* thiz, ::std::int32_t index, ::DotNet::CesiumForUnity::CesiumUintVec4* pReturnValue, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumUintVec4 CesiumUintMat4x4::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumUintVec4 result;
    Property_get_Item(&(*this), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


