#include <DotNet/Unity/Mathematics/float2x2.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Unity/Mathematics/float2.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct float2;
}
namespace DotNet::Unity::Mathematics {
struct float2x2;
}

namespace DotNet::Unity::Mathematics {

void (*float2x2::Construct_nD6FhZgoOnVALNm4NoUCeQ)(const ::DotNet::Unity::Mathematics::float2* c0, const ::DotNet::Unity::Mathematics::float2* c1, ::DotNet::Unity::Mathematics::float2x2* pReturnValue, void** reinteropException) = nullptr;


float2x2 float2x2::Construct(const ::DotNet::Unity::Mathematics::float2& c0, const ::DotNet::Unity::Mathematics::float2& c1)
{
    void* reinteropException = nullptr;
    float2x2 result;
    Construct_nD6FhZgoOnVALNm4NoUCeQ(&c0, &c1, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::Unity::Mathematics::float2x2::Property_get_Item)(const ::DotNet::Unity::Mathematics::float2x2* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float2* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::float2 float2x2::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float2 result;
    Property_get_Item(&(*this), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


